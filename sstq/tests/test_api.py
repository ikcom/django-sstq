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
        self.assertIsSubclass(sstq.TaskStatus, int, "'TaskStatus' should be a subclass of 'int'")
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
