"""
Tests for ThreadedBackend.
"""

import time
from collections.abc import Callable
from threading import Barrier, Event, Thread
from typing import Any

from django.test import TestCase, override_settings

import sstq
from sstq.backends.thread import CancelledError, ThreadedBackend
from sstq.base import Future, TaskDefinition, TaskStatus

THREADED_SETTINGS = sstq.Config(
    default={
        "BACKEND": "sstq.backends.thread.ThreadedBackend",
    }
)

# ---------------------------------------------------------------------------
# Tasks used across tests - must be module-level so they are fully qualified
# ---------------------------------------------------------------------------


def _add(a: int, b: int) -> int:
    return a + b


def _raise_value_error():
    raise ValueError("boom")


# Barrier-controlled tasks for race/cancel tests
_worker_entry_event: Event = Event()  # signals test that worker started the task
_worker_release_barrier: Barrier = Barrier(2)  # test + worker rendez-vous to finish task


def _barrier_task():
    """Block inside the worker until the test lets it through."""
    _worker_entry_event.set()
    _worker_release_barrier.wait(timeout=5)


def _slow_task():
    """Sleep long enough that a short timeout always fires."""
    time.sleep(10)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_task_def(
    backend: "ThreadedBackend[..., Any]", func: Callable[..., Any], name: str
) -> "TaskDefinition[..., Any]":
    """Create a TaskDefinition pre-wired to *backend* so the lazy Django
    backend-handler lookup is never triggered inside worker threads."""
    td: TaskDefinition[..., Any] = TaskDefinition(func, name=name)
    td._backend = backend  # pyright: ignore[reportPrivateUsage]
    return td


# ---------------------------------------------------------------------------
# Basic happy-path tests
# ---------------------------------------------------------------------------


@override_settings(TASKS=THREADED_SETTINGS)
class ThreadedBackendBasicTestCase(TestCase):
    def setUp(self):
        from sstq.config import BackendConfig

        self.backend: ThreadedBackend[..., Any] = ThreadedBackend(
            alias="default", config=BackendConfig(BACKEND="sstq.backends.thread.ThreadedBackend")
        )
        self.addCleanup(self._shutdown)

    def _shutdown(self):
        try:
            self.backend.shutdown(wait=True, timeout=3)
        except Exception:
            pass

    def test_enqueue_returns_future(self):
        """enqueue() must return a Future instance."""
        td = _make_task_def(self.backend, _add, "tests.add")
        future = self.backend.enqueue(td, 1, 2)
        self.assertIsInstance(future, Future)

    def test_result_available_after_completion(self):
        """future.result() blocks and then returns the task's return value."""
        td = _make_task_def(self.backend, _add, "tests.add2")
        future = self.backend.enqueue(td, 3, 4)
        result = self.backend.get_task_result(future, timeout=5)
        self.assertEqual(result, 7)

    def test_failed_task_stores_exception(self):
        """A task that raises must end up FAILED and expose the exception."""
        td = _make_task_def(self.backend, _raise_value_error, "tests.raiser")
        future = self.backend.enqueue(td)
        exc = self.backend.get_task_exception(future, timeout=5)
        self.assertIsInstance(exc, ValueError)
        # FAILED is a terminal state; getting the result must raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.backend.get_task_result(future, timeout=1)

    def test_multiple_tasks_enqueued_in_loop(self):
        """All tasks enqueued in a loop must complete with correct individual results."""
        pairs = [(i, i * 2) for i in range(10)]
        futures = [
            self.backend.enqueue(_make_task_def(self.backend, _add, f"tests.add_loop_{i}"), a, b)
            for i, (a, b) in enumerate(pairs)
        ]
        results = [self.backend.get_task_result(f, timeout=5) for f in futures]
        self.assertEqual(results, [a + b for a, b in pairs])

    def test_worker_is_daemon_thread(self):  # tests I5
        """Worker thread must be a daemon so it does not block process exit."""
        self.assertTrue(self.backend._worker.daemon)  # pyright: ignore[reportPrivateUsage]


# ---------------------------------------------------------------------------
# Cancellation tests
# ---------------------------------------------------------------------------


@override_settings(TASKS=THREADED_SETTINGS)
class ThreadedBackendCancelTestCase(TestCase):
    def setUp(self):
        from sstq.config import BackendConfig

        self.backend: ThreadedBackend[..., Any] = ThreadedBackend(
            alias="default", config=BackendConfig(BACKEND="sstq.backends.thread.ThreadedBackend")
        )
        self.addCleanup(self._shutdown)

    def _shutdown(self):
        try:
            self.backend.shutdown(wait=True, timeout=3)
        except Exception:
            pass

    def _make_td(self, func: Callable[..., Any], name: str) -> TaskDefinition[..., Any]:
        return _make_task_def(self.backend, func, name)

    def test_cancel_available_task_returns_true(self):  # tests I1 fix
        """cancel_task() on an AVAILABLE (not yet running) task must return True."""
        global _worker_entry_event, _worker_release_barrier
        _worker_entry_event = Event()
        _worker_release_barrier = Barrier(2)

        # Hold the worker busy so our target task stays AVAILABLE
        busy_td = self._make_td(_barrier_task, "tests.barrier1a")
        self.backend.enqueue(busy_td)
        _worker_entry_event.wait(timeout=5)  # worker is now inside _barrier_task

        # Enqueue the task we want to cancel while worker is occupied
        target_td = self._make_td(_add, "tests.add_cancel")
        target_future = self.backend.enqueue(target_td, 1, 1)

        result = self.backend.cancel_task(target_future)
        self.assertTrue(result)
        self.assertEqual(target_future._result.status, TaskStatus.CANCELED)  # pyright: ignore[reportPrivateUsage]

        # Release the blocked worker
        _worker_release_barrier.wait(timeout=5)

    def test_cancel_inverted_condition_bug(self):  # exposes I1
        """cancel_task() on a DONE task must return False (not True)."""
        td = self._make_td(_add, "tests.add_done")
        future = self.backend.enqueue(td, 5, 6)
        # Wait for completion
        self.backend.get_task_result(future, timeout=5)
        # Cancelling a finished task must fail
        result = self.backend.cancel_task(future)
        self.assertFalse(result)

    def test_cancel_failed_task_returns_false(self):
        """cancel_task() on a FAILED task must return False."""
        td = self._make_td(_raise_value_error, "tests.raiser_cancel")
        future = self.backend.enqueue(td)
        self.backend.get_task_exception(future, timeout=5)
        result = self.backend.cancel_task(future)
        self.assertFalse(result)

    def test_cancelled_future_result_raises(self):
        """After cancellation, get_task_result() must raise (CancelledError or RuntimeError)."""
        global _worker_entry_event, _worker_release_barrier
        _worker_entry_event = Event()
        _worker_release_barrier = Barrier(2)

        busy_td = self._make_td(_barrier_task, "tests.barrier2a")
        self.backend.enqueue(busy_td)
        _worker_entry_event.wait(timeout=5)

        target_td = self._make_td(_add, "tests.add_cancel2")
        target_future = self.backend.enqueue(target_td, 2, 2)
        self.backend.cancel_task(target_future)

        _worker_release_barrier.wait(timeout=5)

        with self.assertRaises((CancelledError, RuntimeError)):
            self.backend.get_task_result(target_future, timeout=2)


# ---------------------------------------------------------------------------
# Concurrency tests
# ---------------------------------------------------------------------------


@override_settings(TASKS=THREADED_SETTINGS)
class ThreadedBackendConcurrencyTestCase(TestCase):
    def setUp(self):
        from sstq.config import BackendConfig

        self.backend: ThreadedBackend[..., Any] = ThreadedBackend(
            alias="default", config=BackendConfig(BACKEND="sstq.backends.thread.ThreadedBackend")
        )
        self.addCleanup(self._shutdown)

    def _shutdown(self):
        try:
            self.backend.shutdown(wait=True, timeout=3)
        except Exception:
            pass

    def _make_td(self, func: Callable[..., Any], name: str) -> TaskDefinition[..., Any]:
        return _make_task_def(self.backend, func, name)

    def test_cancel_running_task_returns_false(self):  # tests I1 fix boundary
        """cancel_task() on a RUNNING task must return False."""
        global _worker_entry_event, _worker_release_barrier
        _worker_entry_event = Event()
        _worker_release_barrier = Barrier(2)

        td = self._make_td(_barrier_task, "tests.barrier3")
        future = self.backend.enqueue(td)
        _worker_entry_event.wait(timeout=5)  # task is now RUNNING

        result = self.backend.cancel_task(future)
        self.assertFalse(result)

        # Release the worker
        _worker_release_barrier.wait(timeout=5)

    def test_get_result_timeout(self):  # tests I4 fix
        """get_task_result() must raise TimeoutError promptly on a slow task."""
        td = self._make_td(_slow_task, "tests.slow")
        future = self.backend.enqueue(td)
        start = time.monotonic()
        with self.assertRaises(TimeoutError):
            self.backend.get_task_result(future, timeout=0.2)
        elapsed = time.monotonic() - start
        # Should return well within 2s even if it was busy-waiting
        self.assertLess(elapsed, 2.0)

    def test_concurrent_readers_all_get_result(self):  # tests I3/I4 fix
        """Multiple threads calling get_task_result() concurrently must all get the same value."""
        td = self._make_td(_add, "tests.add_concurrent")
        future = self.backend.enqueue(td, 10, 20)

        results: list[int] = []
        errors: list[Exception] = []
        start_barrier = Barrier(10)

        def reader():
            start_barrier.wait(timeout=5)
            try:
                r = self.backend.get_task_result(future, timeout=5)
                results.append(r)
            except Exception as e:
                errors.append(e)

        threads = [Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(errors, [], f"Unexpected errors: {errors}")
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r == 30 for r in results))


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


@override_settings(TASKS=THREADED_SETTINGS)
class ThreadedBackendLifecycleTestCase(TestCase):
    def setUp(self):
        from sstq.config import BackendConfig

        self.backend: ThreadedBackend[..., Any] = ThreadedBackend(
            alias="default", config=BackendConfig(BACKEND="sstq.backends.thread.ThreadedBackend")
        )
        self.addCleanup(self._shutdown)

    def _shutdown(self):
        # Best-effort cleanup in case the test itself didn't call shutdown
        try:
            if self.backend._worker.is_alive():  # pyright: ignore[reportPrivateUsage]
                self.backend.shutdown(wait=True, timeout=3)
        except Exception:
            pass

    def test_shutdown_stops_worker_thread(self):  # tests I6
        """shutdown(wait=True) must join the worker within the timeout."""
        self.assertTrue(self.backend._worker.is_alive())  # pyright: ignore[reportPrivateUsage]
        self.backend.shutdown(wait=True, timeout=3)
        self.assertFalse(self.backend._worker.is_alive())  # pyright: ignore[reportPrivateUsage]

    def test_shutdown_is_idempotent(self):
        """Calling shutdown() twice must not raise."""
        self.backend.shutdown(wait=True, timeout=3)
        try:
            self.backend.shutdown(wait=True, timeout=1)
        except Exception as e:
            self.fail(f"Second shutdown() raised: {e}")
