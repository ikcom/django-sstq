import sstq


def test_func():
    pass


class TestClass:
    def test_method(self):
        pass


def test_nested_func():
    def inner_func():
        pass

    return inner_func


@sstq.task
def test_task():
    return "test_task result"
