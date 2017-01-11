import sys
from contextlib import contextmanager
from ..._compat import reraise

@contextmanager
def end_reraise_context():
    exc_info = sys.exc_info()
    yield
    reraise(*exc_info)
