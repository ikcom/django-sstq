import inspect
from typing import TYPE_CHECKING, Any, Callable, Optional, Self, TypedDict, Unpack, overload
from uuid import UUID, uuid7

from django.db import models
from django.utils.translation import pgettext_lazy

from sstq.utils import is_fully_qualified_function, make_qualified_name

DEFAULT_TASK_PRIORITY = 0
DEFAULT_TASK_QUEUE_NAME = "default"

if TYPE_CHECKING:
    from sstq.backends.base import BaseBackend


class TaskStatus(models.IntegerChoices):
    """Enumeration of possible task statuses in the SSTQ system."""

    AVAILABLE = 10, pgettext_lazy("TaskStatus", "Available")
    """A task is available when it is ready to be executed but has not yet
    been picked up by a worker. This is the initial state of a task after it is enqueued.
    Available tasks can be picked up by workers for execution or
    canceled before they are."""

    RUNNING = 20, pgettext_lazy("TaskStatus", "Running")
    """A task is running as soon as it is picked by a worker.
    It may not have started executing yet, but it's no longer available for other workers to
    pick up and it can't be canceled."""

    CANCELED = 30, pgettext_lazy("TaskStatus", "Canceled")
    """A task is canceled when it has been explicitly canceled while it was still
    available. Canceled tasks will not be picked up by workers and cannot transition
    to other states. A running task cannot be canceled."""

    FAILED = 40, pgettext_lazy("TaskStatus", "Failed")
    """A task has failed if execution was interrupted before a value was returned, either
    due to an exception or because the worker process was terminated.
    Only running tasks can transition to failed.
    """

    DONE = 50, pgettext_lazy("TaskStatus", "Done")
    """A task is done when it has completed execution and returned a value successfully.
    Only running tasks can transition to done."""


class TaskDefinitionOverrideOptions(TypedDict, total=False):
    """Task definition override options that can be specified in :meth:`TaskDefinition.using`."""

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

    backend: Optional[str]
    """The backend alias to use when enqueueing this task.
    If not specified, the default backend will be used."""

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
        self.backend = backend

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Execute the task function with the given arguments."""
        return self.func(*args, **kwargs)

    def enqueue(self, *args: P.args, **kwargs: P.kwargs) -> BoundTask[P, R]:
        """Enqueue this task with the given arguments. This method creates a bound task instance
        that encapsulates the task definition along with the specific arguments for execution.
        """
        return self.get_backend().enqueue(self, *args, **kwargs)

    def using(self, **overrides: Unpack[TaskDefinitionOverrideOptions]) -> Self:
        """Override task definition properties for the next enqueue operation.

        Keyword arguments from :class:`TaskDefinitionOverrideOptions`:

        Parameters
        ----------
        backend : str, Optional
            Override the default backend. The task will be enqueued to the
            specified backend instead of the one defined in this TaskDefinition.
        queue : str, Optional
            Override the default queue. The task will be enqueued to
            the specified queue instead of the one defined in this TaskDefinition.
        priority : int, Optional
            Override the default priority. The task will be enqueued
            with the specified priority instead of the one defined in this TaskDefinition.
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

    def get_backend(self) -> BaseBackend:
        from sstq.backends.dummy import DummyBackend

        return DummyBackend("dummy")


class BoundTask[**P, R]:
    """Represents an enqueued task that is bound to specific parameters and queue order."""

    task_def: TaskDefinition[P, R]
    """The task definition that this bound task is an instance of."""

    args: tuple[Any, ...]
    """The positional arguments that will be passed to the task function when executed."""

    kwargs: dict[str, Any]
    """The keyword arguments that will be passed to the task function when executed."""

    queue_id: UUID
    """A unique identifier for this bound task in the queue.
    This can be used by backends to track and manage the task."""

    def __init__(self, task_def: TaskDefinition[P, R], *args: P.args, **kwargs: P.kwargs) -> None:
        self.task_def = task_def
        self.args = args
        self.kwargs = kwargs
        self.queue_id = uuid7()

    def result(self) -> R:
        """If the backend supports retrieving results,
        this method will return the result of the task execution.
        If the task has not completed yet, this method may block until the result is available.
        """
        raise NotImplementedError("This backend does not support retrieving task results.")


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
