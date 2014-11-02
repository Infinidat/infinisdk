###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
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
    xrange = builtins.xrange
    sorted = builtins.sorted
    cmp = builtins.cmp

else:

    import functools
    import http.client as httplib

    string_types = (str,)

    import builtins

    from io import StringIO
    from configparser import ConfigParser
    import http.client as httplib

    raw_input = input

    zip = builtins.zip
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
        return builtins.sorted(iterable, key=key, reverse=reverse)

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
try:
    from collections import OrderedDict
except ImportError: # python 2.6
    from ordereddict import OrderedDict
