from __future__ import print_function
import itertools
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

_FORBIDDEN_STRINGS = ["infinipy"]

def test_no_infinipy_string():
    errors = []
    pkg_path = os.path.join(_HERE, "..", "infinisdk")
    assert os.path.isdir(pkg_path)
    for path, dirnames, filenames in os.walk(pkg_path):
        for name in itertools.chain(dirnames, filenames):
            _check_forbidden_strings(name, errors)

        for filename in filenames:
            if filename.endswith((".py", ".rst", ".md")):
                with open(os.path.join(path, filename)) as f:
                    for lineno, line in enumerate(f, start=1):
                        line = line.lower()
                        for s in _FORBIDDEN_STRINGS:
                            if s in line:
                                errors.append("{0}, line {1}: contains {2!r}".format(filename, lineno, s))

    for error in errors:
        print(error)
    assert not errors, "Forbidden strings appear in code"

def _check_forbidden_strings(s, errors):
    orig = s
    s = s.lower()
    for forbidden_str in _FORBIDDEN_STRINGS:
        if forbidden_str in s:
            errors.append("{0}: contains {1}".format(orig, forbidden_str))
