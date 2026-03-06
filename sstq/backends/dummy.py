from sstq.base import BoundTask, TaskDefinition

from .base import BaseBackend


class DummyBackend(BaseBackend):
    """A dummy backend that does nothing. Useful for testing and development."""

    def enqueue[**P, T](
        self, task: TaskDefinition[P, T], *args: P.args, **kwargs: P.kwargs
    ) -> BoundTask[P, T]:
        """Simulate enqueuing a task by returning a BoundTask without doing anything."""
        return BoundTask(task, *args, **kwargs)
