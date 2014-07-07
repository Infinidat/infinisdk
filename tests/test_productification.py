from __future__ import print_function
import itertools
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_ROOT = os.path.join(_HERE, "..", "infinisdk")
_DOCS_ROOT = os.path.join(_HERE, "..", "doc")

_FORBIDDEN_STRINGS = [
    "infinipy",  # obviously...
    "infinisdk2",  # results from converting only 'infinipy' to 'infinisdk', forgetting the '2'...
    "purge", # has been moved to infinisdk_internal
]

def test_copyright():
    missing = []
    for path, _, filenames in os.walk(_PKG_ROOT):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            filename = os.path.join(path, filename)
            with open(filename) as f:
                source = f.read()

            if 'Copyright' not in source:
                missing.append(filename)
    assert not missing, "Files are missing copyright notice:\n{0}".format("\n".join(sorted(missing)))

def test_no_infinipy_string():
    errors = []

    for root in (_PKG_ROOT, _DOCS_ROOT):
        assert os.path.isdir(root)
        for path, dirnames, filenames in os.walk(root):
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
