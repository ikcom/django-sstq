from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional

from sstq.base import DEFAULT_TASK_QUEUE_NAME, Future, TaskDefinition, TaskStatus
from sstq.config import BackendConfig


@dataclass
class StatusQueryResult[R]:
    status: TaskStatus
    result: R | None = None
    exception: Optional[BaseException | str] = None


class BaseBackend[**P, R](metaclass=ABCMeta):
    """Base class for task queue backends. All backends must implement
    this interface to be compatible with sstq."""

    supports_priority: bool = False
    """Indicates whether this backend supports task prioritization. If False,
    all tasks will be treated with the same priority regardless of the value
    set in the TaskDefinition."""

    supports_scheduling: bool = False
    """Indicates whether this backend supports scheduling tasks to run at a
    specific time in the future. If False, all tasks will be executed as soon as
    possible regardless of any scheduling parameters."""

    supports_persistent_results: bool = False
    """Indicates whether this backend supports storing of task results that can
    be retrieved after task completion. If False, the backend will not guarantee
    that task results can be retrieved after the result has been read once.
    Subsequent calls to :meth:`get_task_result` may raise an exception if the result
    is no longer available."""

    def __init__(self, alias: str, config: BackendConfig) -> None:
        self.alias = alias
        self.queues = config.get("QUEUES", [DEFAULT_TASK_QUEUE_NAME])

    def enqueue(
        self, task: TaskDefinition[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> Future[P, R]:
        """Enqueue a task for execution."""
        return Future(
            task_def=task,
            params={"args": args, "kwargs": kwargs},
            result=StatusQueryResult(status=TaskStatus.AVAILABLE),
        )

    @abstractmethod
    def _query_task_status(self, task: Future[P, R]) -> StatusQueryResult[R]: ...

    @abstractmethod
    def _get_result(self, task: Future[P, R], timeout: Optional[int | float] = None) -> R: ...

    @abstractmethod
    def _get_exception(
        self, task: Future[P, R], timeout: Optional[int | float] = None
    ) -> BaseException | str | None: ...

    @abstractmethod
    def cancel_task(self, task: Future[P, R]) -> bool:
        """Return True if the attempt to cancel a queued task was successful, False otherwise."""

    def _is_task_terminated_already(self, task: Future[P, R]) -> bool:
        """Check if we already know that the task has reached a terminal state"""
        return task._result.status > TaskStatus.RUNNING  # pyright: ignore[reportPrivateUsage]

    def get_task_result(self, task: Future[P, R], timeout: Optional[int | float] = None) -> R:
        """Retrieve the result of a completed task. If the task has not completed yet,
        this method may block until the result is available or the timeout is reached.
        """

        match (cached := task._result).status:  # pyright: ignore[reportPrivateUsage]
            case TaskStatus.AVAILABLE | TaskStatus.RUNNING:
                return self._get_result(task, timeout)

            case TaskStatus.CANCELED:
                raise RuntimeError("Cannot retrieve result of a canceled task.")

            case TaskStatus.FAILED:
                raise RuntimeError("Cannot retrieve result of a failed task.")

            case TaskStatus.DONE:
                return cached.result  # pyright: ignore[reportReturnType]; cheaper than casting to R

    def get_task_exception(
        self, task: Future[P, R], timeout: Optional[int | float] = None
    ) -> BaseException | str | None:
        """Retrieve the exception raised by a failed task, if available. If the task has not
        failed or if the backend does not support storing exceptions, this method may return None."""

        if self._is_task_terminated_already(task):
            return task._result.exception  # pyright: ignore[reportPrivateUsage]

        return self._get_exception(task, timeout)

    def query_task_status(self, task: Future[P, R]) -> StatusQueryResult[R]:
        """Query the status of a queued task"""
        result = self._query_task_status(task)
        task.set_result(result)  # pyright: ignore[reportDeprecated]
        return result

    def is_task_done(self, task: Future[P, R]) -> bool:
        """Return True if queued task was successfully :term:`canceled <TaskStatus.CANCELED>` or finished :term:`running <TaskStatus.RUNNING>`."""

        if self._is_task_terminated_already(task):
            return task._result.status > TaskStatus.FAILED  # pyright: ignore[reportPrivateUsage]

        return self.query_task_status(task).status > TaskStatus.FAILED

    def is_task_running(self, task: Future[P, R]) -> bool:
        """Return True if the call is currently :term:`running <TaskStatus.RUNNING>`."""

        if self._is_task_terminated_already(task):
            return False

        return self.query_task_status(task).status == TaskStatus.RUNNING

    def is_task_canceled(self, task: Future[P, R]) -> bool:
        if self._is_task_terminated_already(task):
            return task._result.status == TaskStatus.CANCELED  # pyright: ignore[reportPrivateUsage]

        return self.query_task_status(task).status == TaskStatus.CANCELED
