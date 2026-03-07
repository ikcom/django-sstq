from typing import Any, Callable

from django.utils.connection import BaseConnectionHandler
from django.utils.module_loading import import_string

from .backends.base import BaseBackend
from .base import Future, TaskDefinition, TaskStatus, task
from .config import Config
from .exceptions import InvalidTaskBackend

__all__ = [
    "task",
    "TaskDefinition",
    "TaskStatus",
    "Future",
    "Config",
    "backends",
]


class TaskBackendHandler(BaseConnectionHandler):
    settings_name = "TASKS"
    exception_class = InvalidTaskBackend

    def create_connection(self, alias: str) -> BaseBackend[..., Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        params = self.settings[alias]
        backend = params["BACKEND"]
        try:
            backend_cls = import_string(backend)
            return backend_cls(alias, **params)
        except ImportError as e:
            raise InvalidTaskBackend(f"Could not find backend '{backend}': {e}") from e

    __getitem__: Callable[[str], BaseBackend[..., Any]]  # pyright: ignore[reportIncompatibleMethodOverride]


backends = TaskBackendHandler()
