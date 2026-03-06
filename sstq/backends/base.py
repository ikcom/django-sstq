from abc import ABCMeta, abstractmethod
from typing import Any

from sstq.base import BoundTask, TaskDefinition

DEFAULT_TASK_QUEUE_NAME = "default"


class BaseBackend(metaclass=ABCMeta):
    supports_priority: bool = False
    """Indicates whether this backend supports task prioritization. If False,
    all tasks will be treated with the same priority regardless of the value
    set in the TaskDefinition."""

    supports_scheduling: bool = False
    """Indicates whether this backend supports scheduling tasks to run at a
    specific time in the future. If False, all tasks will be executed as soon as
    possible regardless of any scheduling parameters."""

    def __init__(self, alias: str, **params: dict[str, Any]) -> None:
        self.alias = alias
        self.queues = params.get("queues", [DEFAULT_TASK_QUEUE_NAME])

    @abstractmethod
    def enqueue[**P, T](
        self, task: TaskDefinition[P, T], *args: P.args, **kwargs: P.kwargs
    ) -> BoundTask[P, T]:
        """Enqueue a task for execution."""
