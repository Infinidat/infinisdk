from capacity import Capacity
from sentinels import NOTHING
from vintage import deprecated

from .exceptions import MissingFields


def _make_getter(field, name_template):
    def getter(self, **kwargs):
        return self.get_field(field.name, **kwargs)

    getter.__name__ = name_template.format(field.name)
    getter.__doc__ = """Obtains the value of the {0.name!r} field

    :returns: {1}
""".format(field, _format_type_doc(field.type._type))  # pylint: disable=protected-access
    return getter

def make_getter(field):
    name_template = "is_{0}" if field.type._type is bool else "get_{0}"  # pylint: disable=protected-access
    return _make_getter(field, name_template)

def make_updater(field):
    def updater(self, value, **kwargs):
        return self.update_field(field.name, value, **kwargs)

    updater.__name__ = "update_{0}".format(field.name)
    updater.__doc__ = """Updates the value of the {0.name!r} field

    :param value: The new {0.name} value to be set (type: {1})
""".format(field, _format_type_doc(field.type._type))  # pylint: disable=protected-access
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
    if field.type._type is bool:  # pylint: disable=protected-access
        updaters_list = make_enable_disable_methods(field)
        deprecation_msg = "Use {} instead".format("/".join(func.__name__ for func in updaters_list))
        updaters_list.append(deprecated(updater_func, deprecation_msg))
    else:
        updaters_list = [updater_func]
    return updaters_list

def _format_type_doc(_type):
    from .system_object import SystemObject

    if _type is Capacity:
        return '`Capacity <https://github.com/vmalloc/capacity#usage>`_'

    if isinstance(_type, type) and issubclass(_type, SystemObject):
        _type = '{}.{}'.format(_type.__module__, _type.__name__)

    if isinstance(_type, (str, bytes)):
        return ':class:`{0} object <{0}>`'.format(_type.replace(':', '.'))

    return _type.__name__  # pylint: disable=no-member


def get_data_for_object_creation(object_type, system, fields):
    returned = {}
    missing_fields = set()
    extra_fields = fields.copy()
    for field in object_type.fields:
        if field.name not in fields:
            if not field.creation_parameter or field.optional:
                continue

        field_value = extra_fields.get(field.name, NOTHING)
        extra_fields.pop(field.name, None)
        field_api_value = extra_fields.get(field.api_name, NOTHING)
        extra_fields.pop(field.api_name, None)
        if field_value is NOTHING and field_api_value is NOTHING:
            field_value = field.generate_default()
        if field_value is not NOTHING and field_api_value is not NOTHING:
            raise ValueError("Multiple colliding arguments: {} and {}".format(field.name, field.api_name))
        if field_value is NOTHING and field_api_value is NOTHING and system.is_field_supported(field):
            missing_fields.add(field.name)
        if field_value is not NOTHING:
            returned[field.api_name] = field.binding.get_api_value_from_value(
                system, object_type, None, field_value)
        else:
            returned[field.api_name] = field_api_value

    if missing_fields:
        raise MissingFields("Following fields were not specified: {}".format(
            ", ".join(sorted(missing_fields))))
    returned.update(extra_fields)
    return returned
