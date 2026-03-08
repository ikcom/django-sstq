Glossary
--------

.. glossary::
   :sorted:

   backend
      A backend is a class that implements the
      :class:`BaseBackend <sstq.backends.base.BaseBackend>` interface and is responsible
      for queueing, tracking, scheduling and executing the tasks.

   django-sstq
      Django Super Simple Task Queue

   task definition
   task definitions
      A task definition is a Python function decorated with :deco:`sstq.task`.
      By default, it is an instance of :class:`TaskDefinition <sstq.base.TaskDefinition>`.

   bound task
      A bound task is a :term:`task definition` that has been :term:`enqueued`
      with specific arguments and has received a :term:`queue index`.
   
   queue index
      A unique identifier for a :term:`backend` to track the progress and
      result of a :term:`bound task`. The queue index is of type :class:`uuid.UUID`
      v7 as defined in :attr:`sstq.Future.queue_id`

   enqueue
   enqueued
      To enqueue a task is for a backend to add a :term:`task definition` on
      the execution queue and return a :term:`bound task` with a unique
      :term:`queue index`. A task definition can be :term:`enqueued` multiple times,
      resulting in multiple bound tasks with different queue indices.

   TaskStatus.AVAILABLE
      A task is available when it is ready to be executed but has not
      yet been picked up by a :term:`worker`. This is the initial state of a
      task after it is :term:`enqueued`. Available tasks can be picked up by
      workers for execution or canceled before they are.

   TaskStatus.RUNNING
      A task is running as soon as it is picked by a :term:`worker`. It may
      not have started executing yet, but it's no longer
      :term:`available <TaskStatus.AVAILABLE>` for other workers to
      pick up and it can't be canceled.
   
   TaskStatus.CANCELED
      A task is canceled when it has been explicitly canceled while
      it was still :term:`available <TaskStatus.AVAILABLE>`.
      Canceled tasks will not be picked up by :term:`workers` and cannot
      transition to other states. A :term:`running <TaskStatus.RUNNING>`
      or :term:`done <TaskStatus.DONE>` task cannot be canceled.

   TaskStatus.FAILED
      A task has failed if execution was interrupted before a value
      was returned, either due to an uncaught exception or because
      the worker process was terminated. Only :term:`running <TaskStatus.RUNNING>`
      tasks can transition to failed.
    
   TaskStatus.DONE
      A task is done when it has completed execution and returned a
      value, including :data:`None`. Only :term:`running <TaskStatus.RUNNING>`
      tasks can transition to done.

   worker
   workers
      A worker is a process that continuously polls a :term:`backend` for
      :term:`available <TaskStatus.AVAILABLE>` tasks, picks them up for execution,
      and updates their status to :term:`running <TaskStatus.RUNNING>`. After
      executing the task with the provided arguments, the worker
      updates the task's status to either :term:`done <TaskStatus.DONE>` or
      :term:`failed <TaskStatus.FAILED>` depending on whether execution was
      successful or not.