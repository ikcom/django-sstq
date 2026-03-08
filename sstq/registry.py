from types import ModuleType
from typing import Any

from django.utils.module_loading import import_string

from sstq.base import TaskDefinition


class TaskRegistry:
    """A registry for task definitions, keyed by their fully qualified name."""

    def __init__(self) -> None:
        self._registry: dict[str, TaskDefinition[..., Any]] = {}

    def __getitem__(self, key: str) -> TaskDefinition[..., Any]:
        return self._registry[key]

    def __delitem__(self, key: str) -> None:
        del self._registry[key]

    def __iter__(self):
        return iter(self._registry)

    def __len__(self) -> int:
        return len(self._registry)

    def _register_task(self, task: TaskDefinition[..., Any]) -> None:
        """Register a single task definition."""
        if task.name in self._registry:
            if self._registry[task.name] is not task:
                raise ValueError(f"Task name conflict: {task.name} is already registered")
        else:
            self._registry[task.name] = task

    def register(self, *tasks: TaskDefinition[..., Any] | ModuleType | str) -> None:
        """Register task definitions from the given tasks, modules, or module paths."""
        for item in tasks:
            if isinstance(item, TaskDefinition):
                self._register_task(item)

            elif isinstance(item, str):
                module = import_string(item)
                self.register(module)
