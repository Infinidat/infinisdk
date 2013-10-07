import sys

PY2 = sys.version_info[0] == 2

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

    string_types = (basestring,)

    import __builtin__ as _builtins

    from cStringIO import StringIO
    import httplib

    def iteritems(d):
        return d.iteritems() # not dict.iteritems!!! we support ordered dicts as well

    def itervalues(d):
        return d.itervalues()

    from itertools import izip as zip
    xrange = _builtins.xrange
else:

    import http.client as httplib

    string_types = (str,)

    import builtins as _builtins

    from io import StringIO
    import http.client as httplib

    zip = _builtins.zip
    xrange = range

    def iteritems(d):
        return iter(d.items())

    def itervalues(d):
        return iter(d.values())
