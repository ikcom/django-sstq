import inspect
from typing import TYPE_CHECKING, Any, Callable, Optional, Self, TypedDict, Unpack, overload
from uuid import UUID, uuid7
from warnings import deprecated

from django.db import models
from django.utils.translation import pgettext_lazy

from sstq.utils import is_fully_qualified_function, make_qualified_name

DEFAULT_TASK_PRIORITY = 0
DEFAULT_TASK_QUEUE_NAME = "default"
DEFAULT_TASK_BACKEND_ALIAS = "default"
SETTINGS_KEY = "TASKS"

if TYPE_CHECKING:
    from sstq.backends.base import (
        BaseBackend,
        StatusQueryResult,
    )


class TaskStatus(models.IntegerChoices):
    """Enumeration of possible task statuses in the SSTQ system."""

    #: Enqueued task available for execution. See also :term:`TaskStatus.AVAILABLE`
    AVAILABLE = 10, pgettext_lazy("TaskStatus", "Available")

    #: Task is currently running. See also :term:`TaskStatus.RUNNING`
    RUNNING = 20, pgettext_lazy("TaskStatus", "Running")

    #: Task has failed. See also :term:`TaskStatus.FAILED`
    FAILED = 30, pgettext_lazy("TaskStatus", "Failed")

    #: Task has been canceled. See also :term:`TaskStatus.CANCELED`
    CANCELED = 40, pgettext_lazy("TaskStatus", "Canceled")

    #: Task is done. See also :term:`TaskStatus.DONE`
    DONE = 50, pgettext_lazy("TaskStatus", "Done")


class TaskDefinitionOverrideOptions(TypedDict, total=False):
    """Task definition override options that can be specified in :meth:`sstq.TaskDefinition.using`."""

    backend: str
    queue: str
    priority: int


class TaskDefinition[**P, R]:
    """Wraps a function and it's arguments into a task definition. :class:`TaskDefinition` instances
    should not be created directly, but rather through the :deco:`task` decorator.
    """

    func: Callable[P, R]
    """The original function that this task definition wraps."""

    name: str
    """The name of the task. Every task must have a unique name.
    If not provided, it defaults to the fully qualified name of the function."""

    signature: inspect.Signature
    """The signature of the task function."""

    queue: str
    """The name of the queue where this task should be enqueued.
    If not provided, the default queue name will be used."""

    priority: int
    """The priority level for this task. Higher values indicate higher priority."""

    _backend: Optional[BaseBackend[P, R]]

    def __init__(
        self,
        func: Callable[P, R],
        name: Optional[str] = None,
        queue: str = DEFAULT_TASK_QUEUE_NAME,
        priority: int = DEFAULT_TASK_PRIORITY,
        backend: Optional[str] = None,
    ):

        if not is_fully_qualified_function(func):
            raise RuntimeError(
                f"Task was defined in a local scope and cannot be string-imported: {func}"
            )

        self.func = func
        self.name = name or make_qualified_name(func)
        self.signature = inspect.signature(func)
        self.queue = queue
        self.priority = priority
        self._backend_alias = backend

        self._backend = None

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Execute the task function with the given arguments."""
        return self.func(*args, **kwargs)

    def enqueue(self, *args: P.args, **kwargs: P.kwargs) -> Future[P, R]:
        """Enqueue this task with the given arguments. This method creates a bound task instance
        that encapsulates the task definition along with the specific arguments for execution.
        """
        return self.backend.enqueue(self, *args, **kwargs)

    def using(self, **overrides: Unpack[TaskDefinitionOverrideOptions]) -> Self:
        """Override :term:`task definition` properties for the next enqueue operation.

        Parameters
        ----------
        backend : str, Optional
            Backend alias to use for the next enqueue operation.
        queue : str, Optional
            Queue name to use for the next enqueue operation.
        priority : int, Optional
            Priority level to use for the next enqueue operation.

        Returns
        -------
        Self
            A new :term:`task definition` instance with the specified overrides.
        """

        if overrides:
            return type(self)(
                func=self.func,
                **{
                    attname: overrides.get(attname, getattr(self, attname))
                    for attname in TaskDefinitionOverrideOptions.__annotations__
                },
            )

        return self

    @property
    def backend(self) -> BaseBackend[P, R]:
        """The backend instance that this task definition is associated with. This is determined
        by the backend alias specified in the task definition or by the default backend if no
        alias is provided.
        """
        if self._backend is None:
            from sstq import backends

            self._backend = backends[self._backend_alias or DEFAULT_TASK_BACKEND_ALIAS]

        return self._backend


class BoundParameters(TypedDict):
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class Future[**P, R]:
    """Represents an enqueued task that is bound to specific parameters and queue order."""

    task_def: TaskDefinition[P, R]
    """The task definition that this bound task is an instance of."""

    params: BoundParameters
    """The parameters that will be passed to the task function when executed."""

    queue_id: UUID
    """A unique identifier for this bound task in the queue.
    This can be used by backends to track and manage the task."""

    _result: StatusQueryResult[R]

    def __init__(
        self,
        task_def: TaskDefinition[P, R],
        params: BoundParameters,
        result: StatusQueryResult[R],
    ) -> None:
        self.task_def = task_def
        self.params = params
        self.queue_id = uuid7()
        self._result = result

    def result(self, timeout: Optional[int | float] = None) -> R:
        """Retrieve the result of this enqueued task, blocking until the result is available
        or timeout is reached. If the task"""
        return self.task_def.backend.get_task_result(self, timeout=timeout)

    def exception(self, timeout: Optional[int | float] = None) -> BaseException | str | None:
        return self.task_def.backend.get_task_exception(self, timeout=timeout)

    @deprecated("set_result should only be used by backends")
    def set_result(self, result: StatusQueryResult[R]) -> None:
        """This method should be used only by backends."""
        self._result = result

    def running(self) -> bool:
        """Check if the task is currently :term:`running`."""
        return self.task_def.backend.is_task_running(self)

    def done(self) -> bool:
        """Return True if queued task was successfully :term:`cancelled` or finished :term:`running`."""
        return self.task_def.backend.is_task_done(self)

    def cancelled(self) -> bool:
        """Return True if queued task was successfully :term:`cancelled`."""
        return self.task_def.backend.is_task_canceled(self)

    def cancel(self) -> bool:
        """Attempt to cancel the task if it has not started running yet. The actual cancellation
        behavior depends on the backend implementation and may not be guaranteed.
        """
        return self.task_def.backend.cancel_task(self)


@overload
def task[**P, R](
    *,
    name: Optional[str] = None,
    queue: str = DEFAULT_TASK_QUEUE_NAME,
    priority: int = DEFAULT_TASK_PRIORITY,
) -> Callable[[Callable[P, R]], TaskDefinition[P, R]]: ...
@overload
def task[**P, R](func: Callable[P, R]) -> TaskDefinition[P, R]: ...
def task[**P, R](
    func: Optional[Callable[P, R]] = None,
    *,
    name: Optional[str] = None,
    queue: str = DEFAULT_TASK_QUEUE_NAME,
    priority: int = DEFAULT_TASK_PRIORITY,
) -> Callable[[Callable[P, R]], TaskDefinition[P, R]] | TaskDefinition[P, R]:
    """Decorator for registering a function as a task that can be queued and executed.
    This decorator can be used with paranthesis ``@task()`` or without ``@task``. It registers a
    callable as a task definition with optional configuration for queue, priority, and naming.

    Parameters
    ----------
    func : Callable[P, R], Optional
        The function to be registered as a task. When used as a decorator with
        arguments, this will be None initially.
    name : str, Optional
        An application-wide unique custom name for the task.
        If not provided, the function's fully qualified name will be used.
    queue : str, Optional
        The name of the queue where this task should be enqueued.
        If not provided, the default queue name will be used.
        Defaults to DEFAULT_TASK_QUEUE_NAME.
    priority : int, Optional
        The priority level for this task. Lower values indicate higher priority.
        Defaults to DEFAULT_TASK_PRIORITY.

    Returns
    -------
    TaskDefinition[P, R] | Callable[[Callable[P, R]], TaskDefinition[P, R]]
        If func is provided directly, returns a TaskDefinition instance.
        If used as a decorator with arguments, returns a decorator function that
        accepts a callable and returns a TaskDefinition.

    Examples
    --------
    As a simple decorator without arguments

    >>> @task
    ... def my_function():
    ...     pass

    As a decorator with arguments:

    >>> @task(name='custom_name', queue='high_priority', priority=1)
    ... def my_function():
    ...     pass

    Programmatically:

    >>> def my_function():
    ...     pass
    >>> task_def = task(my_function)
    """

    if func is None:

        def decorator(func: Callable[P, R]) -> TaskDefinition[P, R]:
            return TaskDefinition(func, name=name, queue=queue, priority=priority)

        return decorator

    return TaskDefinition(func, name=name, queue=queue, priority=priority)
