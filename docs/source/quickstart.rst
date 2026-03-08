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

Add ``sstq`` to ``INSTALLED_APPS``:

.. code-block:: python

   INSTALLED_APPS = [
       ...,
       "sstq",
   ]

To use the model backend, also add ``sstq.backends.model`` and run migrations:

.. code-block:: python

   INSTALLED_APPS = [
       ...,
       "sstq",
       "sstq.backends.model",
   ]

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
