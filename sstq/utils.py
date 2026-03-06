import inspect
from typing import Any, Callable


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
