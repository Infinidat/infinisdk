from api_object_schema import Field as FieldBase
from sentinels import NOTHING

from .bindings import InfiniSDKBinding
from .exceptions import AttributeAlreadyExists
from .field_filter import FieldFilter
from .field_sorting import FieldSorting
from .system_object_utils import make_getter, make_field_updaters
from .utils import DONT_CARE


class Field(FieldBase):
    """
    This class represents a single field exposed by a schema
    """
    def __repr__(self):
        # pylint: disable=no-member
        extra = []
        if self.creation_parameter:
            extra.append('Creation param')
        if self.mutable:
            extra.append('Mutable')
        return "<FIELD {}{}>".format(
            self.name,
            ' ({})'.format(', '.join(extra)) if extra else ''
        )

    def __init__(self, *args, **kwargs):
        hidden = kwargs.pop("hidden", False)
        cached = kwargs.pop("cached", NOTHING)
        add_getter = kwargs.pop("add_getter", True)
        add_updater = kwargs.pop("add_updater", True)
        use_in_repr = kwargs.pop("use_in_repr", False)
        feature_name = kwargs.pop("feature_name", NOTHING)
        new_to_version = kwargs.pop("new_to", None)
        until_version = kwargs.pop("until", None)
        toggle_name = kwargs.pop("toggle_name", None)
        super(Field, self).__init__(*args, **kwargs)

        if self.is_identity:  # pylint: disable=no-member
            assert cached in (NOTHING, True), "Identity field must be cached"
            cached = True
        elif cached is NOTHING:
            cached = DONT_CARE
        #:Specifies if this field is returns though system API
        self.hidden = hidden
        #:Specifies if this field is cached by default
        self.cached = cached
        #:Specifies if this field needs to have get function (there is no need to add getter for hidden fields)
        self.add_getter = add_getter and not hidden
        #:Specifies the field getter name if it has one
        self.getter_name = None
        #:Specifies if this field needs to have update function
        self.add_updater = add_updater and self.mutable  # pylint: disable=no-member
        #:Specifies that the object's __repr__ method should use this field to describe the object
        self.use_in_repr = use_in_repr
        #:Specifies the feature this field depended on (new/deprecated since version)
        self.feature_name = feature_name
        #:Specifies the version this field was added
        self.new_to_version = new_to_version
        #:Specifies the version this field is deprecated since
        self.until_version = until_version
        #:Specifies the name for auto-updater: enable_toggle_name & disable_toggle_name will be added to the object
        if toggle_name:
            assert self.type.type is bool  # pylint: disable=no-member
            assert self.mutable  # pylint: disable=no-member
        else:
            if self.add_updater:
                toggle_name = self.name  # pylint: disable=no-member
        self.toggle_name = toggle_name

    def notify_added_to_class(self, cls):
        if self.add_getter:
            getter_func = make_getter(self)
            self.getter_name = getter_func.__name__
            if self.getter_name in cls.__dict__:
                raise AttributeAlreadyExists(cls, self.getter_name)
            setattr(cls, self.getter_name, getter_func)

        if self.add_updater:
            for updater_func in make_field_updaters(self):
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

    def extract_from_json(self, obj_class, json):  # pylint: disable=unused-argument
        # pylint: disable=no-member
        return json[self.api_name]

def _install_filter_factory(operator_name, operator_function_name):
    def meth(self, other):
        return FieldFilter(self, operator_name, other)
    meth.__name__ = operator_function_name
    setattr(Field, operator_function_name, meth)
    return meth

def _install_filter_factories():
    # Installing operators that python has overloading functions for them
    # between operators exists as __between__ for backward compatibility only
    for operator_name in ["eq", "gt", "lt", "ge", "le", "ne", "between"]:
        operator_function_name = "__{}__".format(operator_name)
        _install_filter_factory(operator_name, operator_function_name)

    # Installing operators that python doesn't have overloading functions for them
    for operator_name, operator_function_name in [("in", "in_"),
                                                  ("notin", "not_in"),
                                                  ("between", "between"),
                                                  ("like", "like"),
                                                  ("is", "is_"),
                                                  ("isnot", "is_not")]:
        _install_filter_factory(operator_name, operator_function_name)

_install_filter_factories()
