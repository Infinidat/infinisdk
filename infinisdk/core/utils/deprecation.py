###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
import functools
import sys
from logbook import Logger

from ..._compat import string_types

_deprecation_logger = Logger("deprecation")
_deprecation_locations = set()


def forget_deprecation_locations():
    _deprecation_locations.clear()


class _DeprecatedFunction(object):

    def __init__(self, func, message, obj=None, objtype=None):
        super(_DeprecatedFunction, self).__init__()
        if isinstance(func, classmethod):
            if hasattr(func, '__func__'):
                func = func.__func__
            else:
                func = func.__get__(True)
        self._func = func
        self._message = message
        self._obj = obj
        self._objtype = objtype
        self.__name__ = func.__name__

    def __call__(self, *args, **kwargs):
        caller_location = _get_caller_location()
        if caller_location not in _deprecation_locations:
            warning = "{0} is deprecated.".format(self._get_func_str())
            if self._message is not None:
                warning += " {0}".format(self._message)
            _deprecation_logger.warning(warning, frame_correction=+1)
            _deprecation_locations.add(caller_location)
        if self._obj is not None:
            return self._func(self._obj, *args, **kwargs)
        return self._func(*args, **kwargs)

    def _get_func_str(self):
        if self._objtype is not None:
            return '{0}.{1}'.format(self._objtype.__name__, self._func.__name__)
        return '{0}.{1}'.format(self._func.__module__, self._func.__name__)

    def __get__(self, obj, objtype):
        return self.bound_to(obj, objtype)

    def bound_to(self, obj, objtype):
        return _DeprecatedFunction(self._func, self._message, obj=obj, objtype=objtype)

    @property
    def __doc__(self):
        returned = self._func.__doc__
        if returned:  # pylint: disable=no-member
            returned += "\n.. deprecated\n"  # pylint: disable=no-member
            if self._message:
                returned += "   {0}".format(self._message)  # pylint: disable=no-member
        return returned



def deprecated(func=None, message=None):
    """Marks the specified function as deprecated, and emits a warning when it's called
    """
    if isinstance(func, string_types):
        assert message is None
        message = func
        func = None

    if func is None:
        return functools.partial(deprecated, message=message)

    return _DeprecatedFunction(func, message)


def _get_caller_location(stack_climb=2):
    frame = sys._getframe(stack_climb)  # pylint: disable=protected-access
    try:
        return (frame.f_code.co_name, frame.f_lineno)
    finally:
        del frame
