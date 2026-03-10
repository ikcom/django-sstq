from itertools import count
from queue import Empty, PriorityQueue
from threading import Event, Lock, Thread
from typing import Optional
from weakref import WeakKeyDictionary

from sstq.base import Future, TaskDefinition, TaskStatus
from sstq.config import BackendConfig

from .base import BaseBackend, StatusQueryResult


class CancelledError(Exception):
    """When a result or exception read is attempted on a cancelled task"""


class ThreadedBackend[**P, R](BaseBackend[P, R]):
    def __init__(self, alias: str, config: BackendConfig) -> None:
        super().__init__(alias, config)
        self._queue: PriorityQueue[tuple[int, int, Future[P, R]]] = PriorityQueue()
        self._enqueue_counter = count()
        self._worker = Thread(target=self._worker_loop, daemon=True)
        self._stop_event = Event()
        # One Event per live Future; auto-GC'd when the Future is collected
        self._done_events: WeakKeyDictionary[Future[P, R], Event] = WeakKeyDictionary()
        # Serialises the (check-status → write-status) transitions in the
        # worker and in cancel_task, making them atomic (fixes I2, I3)
        self._transition_lock = Lock()
        self._worker.start()

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                _, _, task = self._queue.get(timeout=0.1)
            except Empty:
                continue

            # cancel_task cannot sneak in between the check and the write.
            with self._transition_lock:
                if task._result.status == TaskStatus.CANCELED:  # pyright: ignore[reportPrivateUsage]
                    # Already cancelled by the client; skip
                    continue
                task.set_result(StatusQueryResult(status=TaskStatus.RUNNING))  # pyright: ignore[reportDeprecated]

            try:
                result = task.task_def.func(*task.params.args, **task.params.kwargs)
                task.set_result(StatusQueryResult(status=TaskStatus.DONE, result=result))  # pyright: ignore[reportDeprecated]
            except Exception as exc:
                task.set_result(StatusQueryResult(status=TaskStatus.FAILED, exception=exc))  # pyright: ignore[reportDeprecated]

            # Signal any threads waiting in _get_result / _get_exception (fixes I4)
            if (event := self._done_events.get(task)) is not None:
                event.set()

    def enqueue(
        self, task: TaskDefinition[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> Future[P, R]:
        future = super().enqueue(task, *args, **kwargs)
        # Register the completion event before putting the task on the queue
        # so the worker always finds it when it signals completion.
        self._done_events[future] = Event()
        self._queue.put((task.priority, next(self._enqueue_counter), future))
        return future

    def _query_task_status(self, task: Future[P, R]) -> StatusQueryResult[R]:
        return task._result  # pyright: ignore[reportPrivateUsage]

    def _get_result(self, task: Future[P, R], timeout: Optional[int | float] = None) -> R:
        event = self._done_events.get(task)
        if event is not None:
            event.wait(timeout=timeout)

        if task._result.status == TaskStatus.CANCELED:  # pyright: ignore[reportPrivateUsage]
            raise CancelledError("Cannot retrieve result of a cancelled task.")
        if not self._is_task_terminated_already(task):
            raise TimeoutError("Timeout while waiting for task result.")
        return task._result.result  # pyright: ignore[reportPrivateUsage, reportReturnType]

    def _get_exception(
        self, task: Future[P, R], timeout: Optional[int | float] = None
    ) -> BaseException | str | None:
        event = self._done_events.get(task)
        if event is not None:
            event.wait(timeout=timeout)

        if task._result.status == TaskStatus.CANCELED:  # pyright: ignore[reportPrivateUsage]
            raise CancelledError("Cannot retrieve exception of a cancelled task.")
        if not self._is_task_terminated_already(task):
            raise TimeoutError("Timeout while waiting for task exception.")
        return task._result.exception  # pyright: ignore[reportPrivateUsage]

    def cancel_task(self, task: Future[P, R]) -> bool:
        with self._transition_lock:
            if task._result.status == TaskStatus.AVAILABLE:  # pyright: ignore[reportPrivateUsage]
                task.set_result(StatusQueryResult(status=TaskStatus.CANCELED))  # pyright: ignore[reportDeprecated]
                # Wake any waiting threads so they see the CANCELED status
                if (event := self._done_events.get(task)) is not None:
                    event.set()
                return True
        return False

    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """Stop the worker thread.  Safe to call multiple times (idempotent).

        Parameters
        ----------
        wait : bool
            If True, block until the worker thread exits.
        timeout : float, Optional
            Maximum seconds to wait for the worker to stop.
        """
        self._stop_event.set()
        if wait and self._worker.is_alive():
            self._worker.join(timeout=timeout)
