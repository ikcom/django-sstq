Task Definition
===============

This section describes how to design tasks and structure task modules.

Functions
---------

Function-based tasks are a good default for stateless background jobs.

Methods
-------

Method-based tasks are a good choice for namespacing related tasks together.

.. warning::
    As of now, this is an untested feature and may not work as expected.
    Use with caution.

Discovery
---------

Apps must explicitly expose :term:`task definitions` to be used. This library
will not automatically discover tasks on account of explicit is better than implicit.

To expose tasks use the :func:`sstq.register` which takes positional arguments
of task definitions, modules, or dotted paths to them. For example:

The preferred way to do this is to use the `ready` method of your app's `AppConfig`:

.. code-block:: python

    import sstq
    from django.apps import AppConfig

    class PollsConfig(AppConfig):
        name = "polls"

        def ready(self):
            sstq.register("polls.tasks")
