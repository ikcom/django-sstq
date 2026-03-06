from django.test import TestCase


class UtilsTestCase(TestCase):
    def test_make_qualified_name(self):
        from sstq.utils import make_qualified_name

        def sample_function():
            pass

        qualified_name = make_qualified_name(sample_function)
        expected_name = f"{sample_function.__module__}.{sample_function.__qualname__}"
        self.assertEqual(
            qualified_name, expected_name, "The qualified name should be correctly generated"
        )

        # Mock a function with no __qualname__ attribute
        class MockFunction:
            def __init__(self):
                self.__name__ = "mock_function"

            def __call__(self):
                pass

        mock_function = MockFunction()
        qualified_name = make_qualified_name(mock_function)
        expected_name = "mock_function"
        self.assertEqual(
            qualified_name,
            expected_name,
            "The qualified name should fall back to __name__ if __qualname__ is not present",
        )

        # Mock a function with a custom __module__ and __qualname__
        class CustomFunction:
            __module__ = "custom.module"
            __qualname__ = "CustomFunction"

        qualified_name = make_qualified_name(CustomFunction)
        expected_name = "custom.module.CustomFunction"
        self.assertEqual(
            qualified_name,
            expected_name,
            "The qualified name should use the custom __module__ and __qualname__ if present",
        )

    def test_is_fully_qualified_function(self):
        from sstq.utils import is_fully_qualified_function

        from . import module

        self.assertTrue(
            is_fully_qualified_function(module.test_func),
            "A module-level function should be considered fully qualified",
        )

        self.assertTrue(
            is_fully_qualified_function(module.TestClass.test_method),
            "A class method should be considered fully qualified",
        )

        self.assertFalse(
            is_fully_qualified_function(module.test_nested_func()),
            "A nested function should not be considered fully qualified",
        )
