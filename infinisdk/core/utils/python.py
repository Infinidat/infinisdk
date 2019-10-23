import sys
from contextlib import contextmanager


def cmp(x, y):
    if x > y:
        return 1
    elif x < y:
        return -1
    return 0


def reraise(_, value, tb=None):
    if value.__traceback__ is not tb:
        raise value.with_traceback(tb)
    raise value


@contextmanager
def end_reraise_context():
    exc_info = sys.exc_info()
    yield
    reraise(*exc_info)
