from django.test import TestCase


class APITestCase(TestCase):
    """Tests for package API"""

    def test_task_import(self):
        import sstq

        self.assertTrue(hasattr(sstq, "task"), "'sstq' should expose 'task' decorator")
        self.assertTrue(
            hasattr(sstq, "TaskDefinition"), "'sstq' should expose 'TaskDefinition' class"
        )
        self.assertTrue(hasattr(sstq, "TaskStatus"), "'sstq' should expose 'TaskStatus' class")
        self.assertTrue(hasattr(sstq, "Future"), "'sstq' should expose 'Future' class")
        self.assertTrue(hasattr(sstq, "Config"), "'sstq' should expose 'Config' utility")
        self.assertTrue(
            hasattr(sstq, "backends"), "'sstq' should expose 'backends' connection handler"
        )

    def test_task_status(self):
        import sstq

        self.assertTrue(hasattr(sstq, "TaskStatus"), "'sstq' should expose 'TaskStatus' class")
        self.assertTrue(
            issubclass(sstq.TaskStatus, int),  # pyright: ignore[reportUnnecessaryIsInstance]
            "'TaskStatus' should be a subclass of 'int'",
        )
        self.assertTrue(
            hasattr(sstq.TaskStatus, "AVAILABLE"), "'TaskStatus' should have 'AVAILABLE' status"
        )
        self.assertTrue(
            hasattr(sstq.TaskStatus, "RUNNING"), "'TaskStatus' should have 'RUNNING' status"
        )
        self.assertTrue(
            hasattr(sstq.TaskStatus, "CANCELED"), "'TaskStatus' should have 'CANCELED' status"
        )
        self.assertTrue(
            hasattr(sstq.TaskStatus, "FAILED"), "'TaskStatus' should have 'FAILED' status"
        )
        self.assertTrue(hasattr(sstq.TaskStatus, "DONE"), "'TaskStatus' should have 'DONE' status")


def test_func():
    return "test_task result"


class TaskRegistryTestCase(TestCase):
    """Tests for TaskRegistry"""

    def test_registry_import(self):
        import sstq

        self.assertTrue(
            hasattr(sstq.TaskRegistry, "register"), "'TaskRegistry' should have 'register' method"
        )
        registry = sstq.TaskRegistry()

        with self.assertRaises(
            StopIteration, msg="Iterating over an empty registry should raise StopIteration"
        ):
            next(iter(registry))

        test_task = sstq.task(test_func)

        registry.register(test_task)

        test_task_duplicate = sstq.task(test_func)
        with self.assertRaises(
            ValueError, msg="Registering a task with a duplicate name should raise ValueError"
        ):
            registry.register(test_task_duplicate)

        self.assertEqual(len(registry), 1, "Registry should have one task after registration")

        task_in_registry = registry[test_task.name]
        self.assertIs(task_in_registry, test_task, "Registered task should be retrievable by name")
        self.assertIn(test_task.name, registry, "Registered task should be in the registry")

        del registry[test_task.name]
        self.assertNotIn(test_task.name, registry, "Deleted task should not be in the registry")

    def test_registry_invalid_registration(self):
        import sstq

        registry = sstq.TaskRegistry()

        with self.assertRaises(TypeError, msg="Registering an invalid item should raise TypeError"):
            registry.register(123)  # type: ignore[arg-type]

    def test_registry_module_registration(self):
        import sstq
        from sstq.tests import module

        registry = sstq.TaskRegistry()
        registry.register("sstq.tests.module")

        self.assertIn(
            "sstq.tests.module.test_task", registry, "Tasks from the module should be registered"
        )

        registry = sstq.TaskRegistry()
        registry.register(module)
        self.assertIn(
            "sstq.tests.module.test_task", registry, "Tasks from the module should be registered"
        )
