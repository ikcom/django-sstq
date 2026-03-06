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

    def test_task_definition_override_options(self):
        from sstq.base import TaskDefinition, TaskDefinitionOverrideOptions

        override_options = set(TaskDefinitionOverrideOptions.__annotations__.keys())
        task_properties = set(TaskDefinition.__annotations__.keys())

        non_task_definition_options = override_options - task_properties

        self.assertSetEqual(
            non_task_definition_options,
            set(),
            "All TaskDefinitionOverrideOptions must be properties of TaskDefinition",
        )
