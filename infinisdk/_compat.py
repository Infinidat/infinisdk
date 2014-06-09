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

    def iterkeys(d):
        return d.iterkeys()

    from itertools import izip as zip
    xrange = _builtins.xrange
    sorted = _builtins.sorted
    cmp = _builtins.cmp

else:

    import functools
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

    def iterkeys(d):
        return iter(d.key())

    def sorted(iterable, cmp=None, key=None, reverse=False):
        if cmp is not None:
            key=functools.cmp_to_key(cmp)
        return _builtins.sorted(iterable, key=key, reverse=reverse)

    def cmp(x, y):
        if x > y:
            return 1
        elif x < y:
            return -1
        return 0


if sys.version_info < (2, 7):

    def get_timedelta_total_seconds(d):
        return d.seconds

else:

    def get_timedelta_total_seconds(d):
        return d.total_seconds()
