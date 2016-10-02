import sys

PY2 = sys.version_info[0] == 2

# pylint: disable=exec-used, redefined-builtin, import-error, no-name-in-module, unused-import, undefined-variable

if PY2:
    exec("""def with_metaclass(meta):
    class _WithMetaclassBase(object):
        __metaclass__ = meta
    return _WithMetaclassBase
""")
else:
    exec("""def with_metaclass(meta):
    class _WithMetaclassBase(object, metaclass=meta):
        pass
    return _WithMetaclassBase
""")

if PY2:

    import httplib

    string_types = (basestring, )


    import __builtin__ as builtins

    from cStringIO import StringIO
    from ConfigParser import ConfigParser
    import httplib

    raw_input = builtins.raw_input

    def iteritems(d):
        return d.iteritems() # not dict.iteritems!!! we support ordered dicts as well

    def itervalues(d):
        return d.itervalues()

    def iterkeys(d):
        return d.iterkeys()

    from itertools import izip as zip
    from itertools import izip_longest
    xrange = builtins.xrange
    sorted = builtins.sorted
    cmp = builtins.cmp

    from contextlib2 import ExitStack

    from urllib import unquote as unquote_url

else:

    import functools
    import http.client as httplib

    string_types = (str, bytes)

    import builtins

    from io import StringIO
    from configparser import ConfigParser
    import http.client as httplib

    from itertools import zip_longest as izip_longest

    raw_input = input

    zip = builtins.zip
    xrange = range

    def iteritems(d):
        return iter(d.items())

    def itervalues(d):
        return iter(d.values())

    def iterkeys(d):
        return iter(d.keys())

    def sorted(iterable, cmp=None, key=None, reverse=False):
        if cmp is not None:
            key = functools.cmp_to_key(cmp)
        return builtins.sorted(iterable, key=key, reverse=reverse)

    def cmp(x, y):
        if x > y:
            return 1
        elif x < y:
            return -1
        return 0

    from contextlib import ExitStack

    from urllib.parse import unquote as unquote_url

if PY2:
    #Yucky, but apparently that's the only way to do this
    exec("""
def reraise(tp, value, tb=None):
    raise tp, value, tb
""", locals(), globals())
else:
    def reraise(tp, value, tb=None):  # pylint: disable=unused-argument
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

try:
    import infi_requests as requests
except ImportError:
    import requests
    from requests.exceptions import RequestException
    from requests.packages.urllib3.exceptions import ProtocolError
else:
    from infi_requests.exceptions import RequestException
    from infi_requests.packages.urllib3.exceptions import ProtocolError
