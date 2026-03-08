Quick Start
===========

Use this guide to install ``django-sstq``, configure it, and define your first
task.

Installation
------------

Install the package:

.. code-block:: bash

   pip install django-sstq

Configuration
-------------

Add ``sstq`` to :setting:`INSTALLED_APPS`.

.. code-block:: python

   INSTALLED_APPS = [
       ... ,
       "sstq",
       "sstq.backends.model", # Optional, only if you want to use the model backend
   ]

.. code-block:: python
   
   # myproject/settings.py

   from sstq import Config
   
   ...

    TASKS = sstq.Config(
        default={
            "BACKEND": "sstq.backends.threaded.ThreadedBackend",
        },
        model={
            "BACKEND": "sstq.backends.model.ModelBackend",
        },
    )

Run migrations if you want to use the :term:`model backend`:

.. code-block:: bash

   python manage.py migrate sstq.backends.model


Task Definition
---------------

Define a task with the :deco:`sstq.task` decorator:

.. code-block:: python

   from sstq import task

   @task
   def add(x, y):
       return x + y
