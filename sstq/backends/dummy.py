from sstq.base import Future, TaskDefinition

from .base import BaseBackend


class DummyBackend[**P, R](BaseBackend[P, R]):
    def enqueue(
        self, task: TaskDefinition[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> Future[P, R]:
        raise NotImplementedError("DummyBackend does not implement task execution.")
