from importlib import import_module
from types import ModuleType
from typing import Any

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

    def __contains__(self, item: str) -> bool:
        return item in self._registry

    def _register_task(self, task: TaskDefinition[..., Any]) -> None:
        """Register a single task definition."""
        if task.name in self._registry:
            if self._registry[task.name] is not task:
                raise ValueError(f"Task name conflict: {task.name} is already registered")
        else:
            self._registry[task.name] = task

    def register(self, *tasks: TaskDefinition[..., Any] | type | ModuleType | str) -> None:
        """Register task definitions from the given tasks, modules, or module paths."""
        for item in tasks:
            if isinstance(item, TaskDefinition):
                self._register_task(item)

            elif isinstance(item, str):
                module = import_module(item)
                self.register(module)

            elif isinstance(item, ModuleType):
                for value in vars(item).values():
                    if isinstance(value, TaskDefinition):
                        self._register_task(value)  # type: ignore[arg-type]

            else:
                raise TypeError(
                    f"Invalid item type for registration: {type(item).__name__}. "
                    "Expected TaskDefinition, module, or module path string."
                )
