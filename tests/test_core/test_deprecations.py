import pytest
import logbook

from infinisdk.core.utils import deprecated
from infinisdk.core.utils.deprecation import forget_deprecation_locations, get_no_deprecations_context


def test_deprecated_func_called(capture):
    assert deprecated_func(1, 2) == 3


def test_deprecation_message(capture):
    deprecated_func(1, 2)

    [record] = capture.records
    assert "deprecated" in record.message
    assert 'deprecated_func' in record.message


def test_deprecation_with_message(capture):

    @deprecated("use something else instead")
    def func(a, b):
        return a + b

    func(1, 2)

    [record] = capture.records
    assert "use something else instead" in record.message
    assert "func is deprecated" in record.message


def test_no_deprecations(capture):

    @deprecated('msg')
    def func(a, b):
        return a + b

    with get_no_deprecations_context():
        assert func(1, 2) == 3
    assert not capture.records



def _no_decorator(func):
    return func


@pytest.mark.parametrize('use_classmethod', [True, False])
def test_class_deprecation(capture, use_classmethod):

    decorator = classmethod if use_classmethod else _no_decorator

    class Bla(object):

        @deprecated('reason')
        @decorator
        def func(self, a, b):
            if use_classmethod:
                assert issubclass(self, Bla)
            else:
                assert isinstance(self, Bla)

            return a + b

    assert (Bla if use_classmethod else Bla()).func(2, 4) == 6

    [record] = capture.records
    assert 'Bla.func is deprecated' in record.message


def test_deprecations_different_sources(capture):

    def f():
        deprecated_func(1, 2)

    def g():
        deprecated_func(1, 2)

    f()
    g()
    assert len(capture.records) == 2


def test_deprecations_same_sources(capture):

    def f():
        deprecated_func(1, 2)

    f()
    f()
    assert len(capture.records) == 1


def test_name_doc():
    @deprecated
    def some_func():
        """docstring here"""
        pass

    assert some_func.__name__ == 'some_func'
    assert 'docstring here' in some_func.__doc__


def test_doc_update():
    @deprecated('some_message')
    def some_func():
        """docstring here"""
        pass

    some_func.__doc__ = 'new_docstring'

    assert 'docstring here' not in some_func.__doc__
    assert 'new_docstring' in some_func.__doc__
    assert 'some_message' in some_func.__doc__



def test_deprecatd_docstring():

    message = "Use something else instead"

    @deprecated()
    def some_func():
        """This is a function
        """

    @deprecated(message)
    def other_func():
        """This is another function
        """

    assert ".. deprecated" in some_func.__doc__
    assert ".. deprecated\n   {0}".format(message) in other_func.__doc__


@pytest.fixture
def capture(request):
    handler = logbook.TestHandler(level=logbook.WARNING)
    handler.push_application()

    @request.addfinalizer
    def pop():
        handler.pop_application()
    return handler


@deprecated
def deprecated_func(a, b):
    return a + b


@pytest.fixture(autouse=True)
def forget_locations():
    forget_deprecation_locations()
