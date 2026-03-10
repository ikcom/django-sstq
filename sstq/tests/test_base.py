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

    def test_task_definition_override_using(self):
        import sstq
        from sstq.base import TaskDefinitionOverrideOptions

        def sample_task():
            pass

        sample_task.__qualname__ = "sample_task"  # Mock the qualname for testing
        sample_task.__module__ = "test_module"  # Mock the module for testing

        sample_task = sstq.task(sample_task)

        self.assertEqual(
            sample_task.queue,
            sstq.DEFAULT_TASK_QUEUE_NAME,
            f"Default queue should be {sstq.DEFAULT_TASK_QUEUE_NAME=}",
        )
        self.assertEqual(
            sample_task.priority,
            sstq.DEFAULT_TASK_PRIORITY,
            f"Default priority should be {sstq.DEFAULT_TASK_PRIORITY=}",
        )
        self.assertEqual(
            sample_task.backend.alias,
            sstq.DEFAULT_BACKEND_ALIAS,
            f"Default backend alias should be {sstq.DEFAULT_BACKEND_ALIAS=}",
        )

        self.assertEqual(
            sample_task.using(queue="test_queue").queue,
            "test_queue",
            "The 'using' method should override the queue",
        )

        self.assertEqual(
            sample_task.using(priority=5).priority,
            5,
            "The 'using' method should override the priority",
        )

        self.assertEqual(
            sample_task.using(backend="dummy").backend.alias,
            "dummy",
            "The 'using' method should override the backend",
        )

        overrides = TaskDefinitionOverrideOptions(
            queue="custom_queue",
            priority=10,
            backend="dummy",
        )

        overridden_task = sample_task.using(**overrides)

        self.assertTupleEqual(
            (overridden_task.queue, overridden_task.priority, overridden_task.backend.alias),
            (overrides.get("queue"), overrides.get("priority"), overrides.get("backend")),
            "The 'using' method should override all specified options",
        )

        self.assertIs(
            sample_task,
            sample_task.using(),
            "Using with no options should return the same instance",
        )

    def test_task_queue_dummy(self):
        from sstq import task

        def dummy_func():
            return "dummy result"

        dummy_func.__qualname__ = "dummy_task"  # Mock the qualname for testing
        dummy_func.__module__ = "test_module"  # Mock the module for testing

        dummy_task = task(dummy_func).using(backend="dummy")

        self.assertEqual(
            dummy_task(),
            "dummy result",
            "The dummy backend should execute the original function and return its result",
        )

        future = dummy_task.enqueue()

        self.assertEqual(
            future.result(),
            "dummy result",
            "The future should return the result of the dummy task execution",
        )

        self.assertFalse(
            future.running(),
            "The future should not be running when using the dummy backend",
        )

        self.assertTrue(
            future.done(),
            "The future should be done immediately when using the dummy backend",
        )

        self.assertFalse(
            future.cancelled(),
            "The future should not be cancelled when using the dummy backend",
        )

        self.assertEqual(
            future.result(),
            "dummy result",
            "The future should return the result of the dummy task execution",
        )

        self.assertIsNone(
            future.exception(),
            "The future should not have any exceptions when using the dummy backend",
        )

    def test_task_queue_dummy_with_options(self):
        from sstq import task

        def dummy_func():
            return "dummy result with options"

        dummy_func.__qualname__ = "dummy_task_with_options"  # Mock the qualname for testing
        dummy_func.__module__ = "test_module"  # Mock the module for testing

        dummy_task = task(dummy_func).using(backend="dummy", priority=5, queue="test_queue")

        future = dummy_task.enqueue()

        self.assertFalse(
            future.running(),
            "The future should not be running when using the dummy backend",
        )

        self.assertTrue(
            future.done(),
            "The future should be done immediately when using the dummy backend",
        )

        self.assertEqual(
            future.result(),
            "dummy result with options",
            "The future should return the result of the dummy task execution",
        )

        self.assertIsNone(
            future.exception(),
            "The future should not have any exceptions when using the dummy backend",
        )

    def test_task_queue_dummy_that_fails(self):
        from sstq import task

        def failing_func():
            raise ValueError("This task is supposed to fail")

        failing_func.__qualname__ = "failing_task"  # Mock the qualname for testing
        failing_func.__module__ = "test_module"  # Mock the module for testing

        failing_task = task(failing_func).using(backend="dummy")

        future = failing_task.enqueue()

        self.assertEqual(
            str(future.exception()),
            "This task is supposed to fail",
            "The future should raise the original exception when the dummy task execution fails",
        )

        self.assertFalse(
            future.running(),
            "The future that fails should not be running when using the dummy backend",
        )

        self.assertFalse(
            future.done(),
            "The future that fails should not be done when using the dummy backend",
        )

        self.assertFalse(
            future.cancelled(),
            "The future that fails should not be cancelled when using the dummy backend",
        )
