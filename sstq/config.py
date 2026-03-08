from typing import NotRequired, TypedDict


class BackendConfig(TypedDict):
    """A backend configuration."""

    BACKEND: str
    """The fully qualified name of the backend class to use for this task backend."""

    QUEUES: NotRequired[list[str]]
    """A list of queue names that this backend should listen to. If not provided, the backend will listen to the default queue."""


def Config(
    config: dict[str, BackendConfig] = {}, /, **configs: BackendConfig
) -> dict[str, BackendConfig]:
    """An autocomplete helper for :setting:`TASKS` setting."""
    return config | configs
