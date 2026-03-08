Configuration
=============

For convenience, ``django-sstq`` provides a :func:`sstq.Config` function for autocomplete
assisted configuration of :setting:`TASKS` 

.. code-block:: python
   
   # myproject/settings.py

   from sstq import Config
   
   ...

    TASKS = sstq.Config(
        default={
            "BACKEND": "sstq.backends.dummy.DummyBackend",
        }
    )

The following are all the configuration options for :setting:`TASKS`:

.. autoclass:: sstq.config.BackendConfig
    :members:

Backends
--------

The following are the built-in backends provided by ``django-sstq``

ConcurrentBackend
~~~~~~~~~~~~~~~~~

Use ``ConcurrentBackend`` for in-memory concurrent execution use cases.

ModelBackend
~~~~~~~~~~~~

Use ``ModelBackend`` when you need persistent queue state in Django models.

Queue Routing
-------------

Document how task types are routed to queues and workers in your environment.
