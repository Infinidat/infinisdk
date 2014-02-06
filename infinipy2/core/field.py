import operator

from .field_filter import FieldFilter
from .field_sorting import FieldSorting

from api_object_schema import Field as FieldBase

class Field(FieldBase):
    """
    This class represents a single field exposed by a schema
    """

    def __init__(self, *args, **kwargs):
        cached = kwargs.pop("cached", False)
        super(Field, self).__init__(*args, **kwargs)

        #:Specifies if this field is cached by default
        self.cached = cached

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
