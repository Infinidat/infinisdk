from collections import Iterable
from .._compat import string_types

_operator_name_to_sign_str = {
    "eq": '=',
    "gt": '>',
    "lt": '<',
    "ge": '>=',
    "le": '<=',
    "ne": '!='}

class FieldFilter(object):

    def __init__(self, field, operator_name, value):
        super(FieldFilter, self).__init__()
        self.field = field
        self.operator_name = operator_name
        self.value = value

    def _translate(self, value):
        return self.field.binding.get_api_value_from_value(None, None, None, value)

    def add_to_url(self, urlobj):
        if isinstance(self.value, Iterable) and not isinstance(self.value, string_types):
            value = "({0})".format(",".join(str(self._translate(val))
                                            for val in self.value))
        else:
            value = self._translate(self.value)

        if value is None:
            value = 'null'

        return urlobj.add_query_param(self.field.api_name,
                                      "{0}:{1}".format(self.operator_name, value))

    def __str__(self):
        return  "{0.field.api_name}{1}{0.value}".format(
            self, _operator_name_to_sign_str.get(self.operator_name, self.operator_name))

    def __repr__(self):
        return "<{0.__class__.__name__}: {0}>".format(self)
