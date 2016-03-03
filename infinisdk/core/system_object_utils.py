from .._compat import string_types
from capacity import Capacity
from .utils import deprecated


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

def make_enable_disable_methods(field):
    def enable(self, **kwargs):
        return self.update_field(field.name, True, **kwargs)
    def disable(self, **kwargs):
        return self.update_field(field.name, False, **kwargs)
    if field.toggle_name != 'enabled':
        enable.__name__ = "enable_{0}".format(field.toggle_name)
        disable.__name__ = "disable_{0}".format(field.toggle_name)
    enable.__doc__ = "Set the value of the {0.name!r} field to True".format(field)
    disable.__doc__ = "Set the value of the {0.name!r} field to False".format(field)
    return [enable, disable]


def make_field_updaters(field):
    updater_func = make_updater(field)
    if field.type._type is bool:
        updaters_list = make_enable_disable_methods(field)
        deprecation_msg = "Use {0} instead".format("/".join(func.__name__ for func in updaters_list))
        updaters_list.append(deprecated(updater_func, deprecation_msg))
    else:
        updaters_list = [updater_func]
    return updaters_list

def _format_type_doc(_type):
    from .system_object import SystemObject

    if _type is Capacity:
        return '`Capacity <https://github.com/vmalloc/capacity#usage>`_'

    if isinstance(_type, type) and issubclass(_type, SystemObject):
        _type = '{0}.{1}'.format(_type.__module__, _type.__name__)

    if isinstance(_type, string_types):
        return ':class:`{0} object <{0}>`'.format(_type.replace(':', '.'))

    return _type.__name__
