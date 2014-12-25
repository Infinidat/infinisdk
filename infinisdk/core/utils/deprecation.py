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
import functools
import sys
from logbook import Logger

from ..._compat import string_types

_deprecation_logger = Logger("deprecation")
_deprecation_locations = set()


def deprecated(func=None, message=None):
    """Marks the specified function as deprecated, and emits a warning when it's called
    """
    if isinstance(func, string_types):
        assert message is None
        message = func
        func = None

    if func is None:
        return functools.partial(deprecated, message=message)

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        caller_location = _get_caller_location()
        if caller_location not in _deprecation_locations:
            warning = "{func.__module__}.{func.__name__} is deprecated.".format(
                func=func)
            if message is not None:
                warning += " {0}".format(message)
            _deprecation_logger.warning(warning, frame_correction=+1)
            _deprecation_locations.add(caller_location)
        return func(*args, **kwargs)

    if new_func.__doc__:  # pylint: disable=no-member
        new_func.__doc__ += "\n.. deprecated\n"  # pylint: disable=no-member
        if message:
            new_func.__doc__ += "   {0}".format(message)  # pylint: disable=no-member

    return new_func


def _get_caller_location(stack_climb=2):
    frame = sys._getframe(stack_climb)  # pylint: disable=protected-access
    try:
        return (frame.f_code.co_name, frame.f_lineno)
    finally:
        del frame
