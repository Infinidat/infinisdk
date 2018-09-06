from __future__ import print_function
import doctest
import os
from contextlib import contextmanager

import pytest
import gossip

_HERE = os.path.abspath(os.path.dirname(__file__))
_DOCS_ROOT = os.path.abspath(os.path.join(_HERE, "..", "doc"))


def test_sphinx_doctest(doctest_path):
    context_filename = doctest_path + ".doctest_context"
    context = {}
    if os.path.exists(context_filename):
        with open(context_filename) as f:
            exec(f.read(), context)  # pylint: disable=exec-used
    with context.get("doctest_context", _NO_CONTEXT)() as globs:
        globs = dict(globs, print_function=print_function, gossip_token='doctest-token')
        result = doctest.testfile(doctest_path, module_relative=False, globs=globs)
    assert not result.failed
    gossip.unregister_token(globs['gossip_token'])

assert os.path.exists(_DOCS_ROOT)
_DOCTEST_PATHS = list(os.path.join(path, filename)
                      for path, _, filenames in os.walk(_DOCS_ROOT)
                      for filename in filenames
                      if filename.endswith(".rst"))


@pytest.fixture(params=_DOCTEST_PATHS)
def doctest_path(request):
    return request.param


@contextmanager
def _NO_CONTEXT():
    yield {}
