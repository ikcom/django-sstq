Documentation
=============

Welcome to the documentation for :term:`django-sstq`

django-sstq
-----------

`/ˈdʒæŋɡoʊ-stɪk/`

Super Simple Task Queue - a django app that provides a
simple way to run background tasks in your Django project.


Install
-------

To get started, install the package:

.. code-block:: bash

   pip install django-sstq


Then, add ``sstq`` to your Django project's ``INSTALLED_APPS``:

.. code-block:: python
    
   INSTALLED_APPS = [
       ...
       'sstq',
   ]


Model Backend
-------------

To use the ``sstq.backends.model.ModelBackend``, add it to ``INSTALLED_APPS``:
    
.. code-block:: python

   INSTALLED_APPS = [
       ...
       'sstq',
       'sstq.backends.model',
   ]

Then, run the migrations:

.. code-block:: bash

   python manage.py migrate sstq.backends.model


Declaring Tasks
---------------

To define a task, use the :deco:`sstq.task` decorator:

.. code-block:: python

   from sstq import task

   @task
   def add(x, y):
       return x + y

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   self
   source/reference
   source/glossary

