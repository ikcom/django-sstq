from typing import Any

from sstq.backends.base import BaseBackend


class ModelBackend(BaseBackend[..., Any]):
    """A backend that stores task definitions and results in the database using Django models.
    This backend is primarily intended for testing and development purposes, and is not
    optimized for performance or scalability. It is not recommended for production use."""
