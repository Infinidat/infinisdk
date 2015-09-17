###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from .._compat import string_types
from capacity import Capacity
from .utils import deprecated


def make_backwards_compatible_getter(field):
    getter_func = _make_getter(field, "get_{0}")
    return deprecated(getter_func, "Use is_{0} instead".format(field.name))

def _make_getter(field, name_template):
    def getter(self, **kwargs):
        return self.get_field(field.name, **kwargs)

    getter.__name__ = name_template.format(field.name)
    getter.__doc__ = """Obtains the value of the {0.name!r} field

    :returns: {1}
""".format(field, _format_type_doc(field.type._type))
    return getter

def make_getter(field):
    name_template = "is_{0}" if field.type._type is bool else "get_{0}"
    return _make_getter(field, name_template)

def make_updater(field):
    def updater(self, value, **kwargs):
        return self.update_field(field.name, value, **kwargs)

    updater.__name__ = "update_{0}".format(field.name)
    updater.__doc__ = """Updates the value of the {0.name!r} field

    :param value: The new {0.name} value to be set (type: {1})
""".format(field, _format_type_doc(field.type._type))
    return updater

def _format_type_doc(_type):
    from .system_object import SystemObject

    if _type is Capacity:
        return '`Capacity <https://github.com/vmalloc/capacity#usage>`_'

    if isinstance(_type, type) and issubclass(_type, SystemObject):
        _type = '{0}.{1}'.format(_type.__module__, _type.__name__)

    if isinstance(_type, string_types):
        return ':class:`{0} object <{0}>`'.format(_type.replace(':', '.'))

    return _type.__name__
