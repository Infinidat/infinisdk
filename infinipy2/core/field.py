import operator

from .._compat import iteritems
from .type_info import TypeInfo
from .field_filter import FieldFilter
from .field_sorting import FieldSorting
from .value_translator import IdentityTranslator
from sentinels import NOTHING

class Field(object):
    """
    This class represents a single field exposed by a schema
    """

    def __init__(self, name, api_name=None, type=str, mutable=True, forbidden=False, mandatory=False, translator=IdentityTranslator(), is_unique=False, default=NOTHING):
        super(Field, self).__init__()

        #:the name of this field, as will be seen by the Python code interacting with the object(s)
        self.name = name
        if api_name is None:
            api_name = name
        #:the name of this field in the API layer (doesn't have to be the same as *name*)
        self.api_name = api_name
        if not isinstance(type, TypeInfo):
            type = TypeInfo(type)
        #:either the type of the exposed field, or a :class:`.TypeInfo` object specifying type properties
        self.type = type

        #:will this field be editable by the user?
        self.mutable = mutable
        #:If set to True, this field cannot be specified on object creation.
        self.forbidden = forbidden
        #:If set to True, means this field has to be specified to the system for object creation
        self.mandatory = mandatory
        #:translator to be used when passing values to/from the system
        self.translator = translator
        #:If True, means that this field value must be unique across the system
        self.is_unique = is_unique
        #:If specified, will be used to generate defaults for this field if required and not specified by the user.
        #:Can be either a value or a callable generating a default
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
    for operator_name in ["eq", "gt", "lt", "ge", "le", "ne"]:
        _install_filter_factory(operator_name)

_install_filter_factories()
