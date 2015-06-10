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
from .exceptions import AttributeAlreadyExists
from .system_object_utils import make_getter, make_updater, make_backwards_compatible_getter
from .field_filter import FieldFilter
from .field_sorting import FieldSorting
from .utils import DONT_CARE

from api_object_schema import Field as FieldBase
from sentinels import NOTHING
from .bindings import InfiniSDKBinding


class Field(FieldBase):
    """
    This class represents a single field exposed by a schema
    """
    def __repr__(self):
        return "<FIELD {}>".format(self.name)

    def __init__(self, *args, **kwargs):
        cached = kwargs.pop("cached", NOTHING)
        add_getter = kwargs.pop("add_getter", True)
        add_updater = kwargs.pop("add_updater", True)
        use_in_repr = kwargs.pop("use_in_repr", False)
        super(Field, self).__init__(*args, **kwargs)

        if self.is_identity:
            assert cached in (NOTHING, True), "Identity field must be cached"
            cached = True
        elif cached is NOTHING:
            cached = DONT_CARE
        #:Specifies if this field is cached by default
        self.cached = cached
        #:Specifies if this field needs to have get function
        self.add_getter = add_getter
        #:Specifies if this field needs to have update function
        self.add_updater = add_updater and self.mutable
        #:Specifies that the object's __repr__ method should use this field to describe the object
        self.use_in_repr = use_in_repr

    def notify_added_to_class(self, cls):
        if self.add_getter:
            getter_func = make_getter(self)
            getter_name = getter_func.__name__
            if getter_name in cls.__dict__:
                raise AttributeAlreadyExists(cls, getter_name)
            setattr(cls, getter_name, getter_func)

            # For backward compatability
            if getter_name.startswith('is_'):
                deprecated_func = make_backwards_compatible_getter(self)
                deprecated_name = deprecated_func.__name__
                if deprecated_name in cls.__dict__:
                    raise AttributeAlreadyExists(cls, deprecated_name)
                setattr(cls, deprecated_name, deprecated_func)

        if self.add_updater:
            updater_func = make_updater(self)
            updater_name = updater_func.__name__
            if updater_name in cls.__dict__:
                raise AttributeAlreadyExists(cls, updater_name)
            setattr(cls, updater_name, updater_func)

    def get_default_binding_object(self):
        return InfiniSDKBinding()

    def __neg__(self):
        return FieldSorting(self, "-")

    def __pos__(self):
        return FieldSorting(self)

    def extract_from_json(self, obj_class, json):
        return json[self.api_name]  #TODO: Use api_object_schema.binding instead

def _install_filter_factory(operator_name, operator_function_name):
    def meth(self, other):
        return FieldFilter(self, operator_name, other)
    meth.__name__ = operator_function_name
    setattr(Field, operator_function_name, meth)
    return meth

def _install_filter_factories():
    # Installing operators that python has overloading functions for them
    # between operators exists as __between__ for backward compatability only
    for operator_name in ["eq", "gt", "lt", "ge", "le", "ne", "between"]:
        operator_function_name = "__{0}__".format(operator_name)
        _install_filter_factory(operator_name, operator_function_name)

    # Installing operators that python doesn't have overloading functions for them
    for operator_name, operator_function_name in [("in", "in_"),
                                                  ("notin", "not_in"),
                                                  ("between", "between"),
                                                  ("like", "like")]:
        _install_filter_factory(operator_name, operator_function_name)

_install_filter_factories()
