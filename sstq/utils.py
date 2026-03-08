import inspect
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from sstq.base import TaskDefinition


def make_qualified_name(func: Callable[..., Any]) -> str:
    """Generate a qualified name for a function, including the module and class if applicable."""
    if hasattr(func, "__qualname__"):
        return f"{func.__module__}.{func.__qualname__}"
    return func.__name__


def is_fully_qualified_function(func: Callable[..., Any]) -> bool:
    """Check if a function can be string-imported (i.e., it's not defined within another function)."""
    if not inspect.isfunction(func) or inspect.isbuiltin(func):
        return False

    return "<locals>" not in func.__qualname__


def discover_tasks(place: ModuleType | type) -> list["TaskDefinition[..., Any]"]:
    """Discover task definitions in a module or class."""
    from sstq.base import TaskDefinition

    tasks: list[TaskDefinition[..., Any]] = []
    for _, obj in inspect.getmembers(place):
        if isinstance(obj, TaskDefinition):
            tasks.append(obj)  # type: ignore[arg-type]

        elif inspect.isclass(obj):
            tasks.extend(discover_tasks(obj))

    return tasks
