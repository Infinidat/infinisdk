from __future__ import print_function
import itertools
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = os.path.join(_HERE, "..")
_SRC_ROOT = os.path.abspath(os.path.join(_HERE, '..', 'infinisdk')) + '/'
assert os.path.isdir(_SRC_ROOT)

assert not _SRC_ROOT.endswith('//')

_FORBIDDEN_STRINGS = [
    "infinipy",  # obviously...
    # results from converting only 'infinipy' to 'infinisdk', forgetting the
    # '2'...
    "infinisdk2",
    "purge",  # has been moved to infinisdk_internal
]

def test_no_infinipy_string():
    errors = []

    for is_file, filename in _iter_checked_filenames():

        basename = os.path.basename(filename)

        _check_forbidden_strings(filename, basename, errors)

        if not is_file:
            continue

        if basename == _without_pyc(os.path.basename(__file__)):
            # we are allowed to contain 'infinipy' in this file of
            # course
            continue

        with open(filename) as f:
            for lineno, line in enumerate(f, start=1):
                line = line.lower()
                for s in _FORBIDDEN_STRINGS:

                    if s == 'purge' and basename.startswith('test_') or basename == 'conftest.py':
                        continue

                    if s in line:
                        errors.append(
                            "{0}, line {1}: contains {2!r}".format(filename, lineno, s))

    for error in errors:
        print(error)
    assert not errors, "Forbidden strings appear in code"


def _without_pyc(filename):
    if filename.endswith('.pyc'):
        return filename[:-1]
    return filename


def _iter_checked_filenames():
    for path, dirnames, filenames in os.walk(_PROJ_ROOT):

        for excluded in ('.git', '.env', '.tox'):
            if excluded in dirnames:
                dirnames.remove(excluded)

        for dirname in dirnames:
            yield False, os.path.abspath(os.path.join(path, dirname))

        for filename in filenames:
            if filename.endswith(('.py', '.rst', '.md')):
                yield True, os.path.abspath(os.path.join(path, filename))

def _check_forbidden_strings(entity, s, errors):
    orig = s
    s = s.lower()
    for forbidden_str in _FORBIDDEN_STRINGS:
        if forbidden_str in s:
            errors.append("{0}: contains {1}".format(entity, forbidden_str))
