from contextlib import contextmanager
from unittest import TestCase
import doctest
import os

class DocTest(TestCase):

    def test_sphinx_doctests(self):
        for path, _, filenames in os.walk(os.path.join(os.path.dirname(__file__), "..", "doc")):
            for filename in filenames:
                if not filename.endswith(".rst"):
                    continue
                filename = os.path.join(path, filename)
                context_filename = os.path.join(path, filename) + ".doctest_context"
                context = {}
                if os.path.exists(context_filename):
                    with open(context_filename) as f:
                        exec(f.read(), context)
                with context.get("doctest_context", _NO_CONTEXT)() as globs:
                    result = doctest.testfile(filename, module_relative=False, globs=globs)
                if result.failed:
                    self.fail("{0}: {1} tests failed!".format(filename, result.failed))

@contextmanager
def _NO_CONTEXT():
    yield {}
