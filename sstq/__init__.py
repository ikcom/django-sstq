# Some code in this file is inspired and adapted by Django's Tasks framework and
# [RealOrangeOne/django-tasks](https://github.com/RealOrangeOne/django-tasks).

# Third-party attribution and license texts are available in THIRD_PARTY_LICENSES.

from types import ModuleType
from typing import Any, Callable

from django.utils.connection import BaseConnectionHandler
from django.utils.module_loading import import_string

from sstq.registry import TaskRegistry

from .backends.base import BaseBackend
from .base import (
    DEFAULT_BACKEND_ALIAS,
    DEFAULT_TASK_PRIORITY,
    DEFAULT_TASK_QUEUE_NAME,
    Future,
    TaskDefinition,
    TaskStatus,
    task,
)
from .config import Config
from .exceptions import InvalidTaskBackend

__all__ = [
    "task",
    "TaskDefinition",
    "TaskStatus",
    "Future",
    "Config",
    "backends",
    "task_registry",
    "register",
    "DEFAULT_TASK_QUEUE_NAME",
    "DEFAULT_TASK_PRIORITY",
    "DEFAULT_BACKEND_ALIAS",
]


class TaskBackendHandler(BaseConnectionHandler):
    settings_name = "TASKS"
    exception_class = InvalidTaskBackend

    def create_connection(self, alias: str) -> BaseBackend[..., Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        params = self.settings[alias]
        backend = params["BACKEND"]
        try:
            backend_cls = import_string(backend)
            return backend_cls(alias, params)
        except ImportError as e:
            raise InvalidTaskBackend(f"Could not find backend '{backend}': {e}") from e

    __getitem__: Callable[[str], BaseBackend[..., Any]]  # pyright: ignore[reportIncompatibleMethodOverride]


backends = TaskBackendHandler()
task_registry = TaskRegistry()


def register(*tasks: TaskDefinition[..., Any] | ModuleType | str) -> None:
    """Register task definitions with the global registry."""
    task_registry.register(*tasks)
