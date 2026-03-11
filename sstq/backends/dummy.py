from typing import Optional

from sstq.base import Future, TaskDefinition, TaskStatus

from .base import BaseBackend, StatusQueryResult


class DummyBackend[**P, R](BaseBackend[P, R]):
    def enqueue(
        self, task: TaskDefinition[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> Future[P, R]:
        future = super().enqueue(task, *args, **kwargs)
        try:
            result = task.func(*args, **kwargs)
            future._result = StatusQueryResult(status=TaskStatus.DONE, result=result)  # pyright: ignore[reportPrivateUsage]
        except Exception as e:
            future._result = StatusQueryResult(status=TaskStatus.FAILED, exception=e)  # pyright: ignore[reportPrivateUsage]
        return future

    def _query_task_status(self, task: Future[P, R]) -> StatusQueryResult[R]:
        return task._result  # pyright: ignore[reportPrivateUsage]

    def _get_result(self, task: Future[P, R], timeout: Optional[int | float] = None) -> R:
        return task._result.result  # pyright: ignore[reportPrivateUsage,reportReturnType]

    def _get_exception(
        self, task: Future[P, R], timeout: Optional[int | float] = None
    ) -> BaseException | str | None:
        return task._result.exception  # pyright: ignore[reportPrivateUsage]

    def cancel_task(self, task: Future[P, R]) -> bool:
        return False
