from .._compat import string_types

class TypeBinderContainer(object):
    """
    Contains several type binders with a common characteristic. Used to implement system.objects and similar facilities
    """

    def __init__(self, system):
        super(TypeBinderContainer, self).__init__()
        self.system = system
        self._binders_by_class = {}
        self._binders_by_name = {}

    def install(self, object_type):
        binder = object_type.bind(self.system)
        self._binders_by_class[object_type] = binder
        self._binders_by_name[object_type.get_plural_name()] = binder
        assert not hasattr(self.system, object_type.get_plural_name())
        setattr(self.system, object_type.get_plural_name(), binder)

    def __getattr__(self, attr):
        try:
            return self._binders_by_name[attr]
        except LookupError:
            raise AttributeError(attr)

    def __getitem__(self, name):
        if isinstance(name, string_types):
            return self._binders_by_name[name]
        return self._binders_by_class[name]
