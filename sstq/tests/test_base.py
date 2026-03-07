import inspect

from django.test import TestCase


class TaskTestCase(TestCase):
    def test_task_creation(self):
        # Test that a task can be created successfully
        from sstq import TaskDefinition, task

        def sample_task():
            pass

        with self.assertRaises(RuntimeError):
            task(sample_task)  # This should raise an error because it's not fully qualified

        sample_task.__qualname__ = "sample_task"  # Mock the qualname for testing

        sample_task = task(sample_task)

        self.assertIsInstance(sample_task, TaskDefinition)

    def test_basic_task_properties(self):
        from sstq import task

        def sample_task[T](arg: T) -> T:
            return arg

        sample_task.__qualname__ = "sample_task"  # Mock the qualname for testing
        sample_task.__module__ = "test_module"  # Mock the module for testing

        sample_task = task(sample_task)
        self.assertEqual(sample_task.name, "test_module.sample_task")
        self.assertEqual(sample_task.queue, "default")
        self.assertEqual(sample_task.priority, 0)
        self.assertTrue(callable(sample_task), "TaskDefinition instances should be callable")
        self.assertEqual(
            sample_task(42), 42, "Calling the task should execute the original function"
        )


class TaskDefinitionTestCase(TestCase):
    def test_task_definition_override_options(self):
        from sstq.base import TaskDefinition, TaskDefinitionOverrideOptions

        override_options = set(TaskDefinitionOverrideOptions.__annotations__.keys())

        # Get a set of TaskDefinition.__init__ argument names
        task_def_init_args = set(inspect.signature(TaskDefinition).parameters.keys()) - {
            "self",
            "func",
        }

        non_task_definition_options = override_options - task_def_init_args

        self.assertSetEqual(
            non_task_definition_options,
            set(),
            f"TaskDefinitionOverrideOptions must only specify valid options: {task_def_init_args}",
        )
