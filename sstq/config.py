from typing import NotRequired, TypedDict


class BackendConfig(TypedDict):
    BACKEND: str
    """The fully qualified name of the backend class to use for this task backend."""
    QUEUES: NotRequired[list[str]]
    """A list of queue names that this backend should listen to. If not provided, the backend will listen to the default queue."""

    # Additional configuration options can be added here as needed, such as connection parameters,
    # authentication credentials, etc.


Config = dict[str, BackendConfig]
