import operator

from .._compat import iteritems
from .type_info import TypeInfo
from .field_filter import FieldFilter
from .field_sorting import FieldSorting
from sentinels import NOTHING

class Field(object):
    """
    This class represents a single field exposed by a schema
    """

    def __init__(self, name, api_name=None, type=str, mutable=True, forbidden=False, mandatory=False, translator=None, is_unique=False, default=NOTHING):
        """
        :param name: the name of this field, as will be seen by the Python code interacting with the object(s)
        :param api_name: the name of this field in the API layer (doesn't have to be the same as *name*)
        :param type: either the type of the exposed field, or a :class:`.TypeInfo` object specifying type properties
        :param mutable: will this field be editable by the user?
        :param forbidden: If set to True, this field cannot be specified on object creation.
        :param mandatory: If set to True, means this field has to be specified to the system for object creation
        :param translator: translator to be used when passing values to/from the system
        :param is_unique: If True, means that this field value must be unique across the system
        :param default: If specified, will be used to generate defaults for this field if required and not specified by the user
        :paramtype default: Either a value or a callable generating a default
        """
        super(Field, self).__init__()
        self.name = name
        if api_name is None:
            api_name = name
        self.api_name = api_name
        if not isinstance(type, TypeInfo):
            type = TypeInfo(type)
        self.type = type
        self.mutable = mutable
        self.forbidden = forbidden
        self.mandatory = mandatory
        self.translator = None
        self.is_unique = is_unique
        self.default = default

    def __neg__(self):
        return FieldSorting(self, "-")

    def __pos__(self):
        return FieldSorting(self)

def _install_filter_factory(operator_name):
    def meth(self, other):
        return FieldFilter(self, operator_name, other)
    meth.__name__ = "__{0}__".format(operator_name)
    setattr(Field, meth.__name__, meth)
    return meth

def _install_filter_factories():
    for operator_name in ["eq"]:
        _install_filter_factory(operator_name)

_install_filter_factories()
