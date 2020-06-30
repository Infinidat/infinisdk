

class TypeBinderContainer:
    """
    Contains several type binders with a common characteristic. Used to implement system.objects and similar facilities
    """

    def __init__(self, system):
        super(TypeBinderContainer, self).__init__()
        self.system = system
        self._binders_by_class = {}
        self._binders_by_name = {}
        self._binders_by_type_name = {}

    def install(self, object_type):
        binder = object_type.bind(self.system)
        self._binders_by_class[object_type] = binder
        self._binders_by_name[object_type.get_plural_name()] = binder
        self._binders_by_type_name[object_type.get_type_name()] = binder
        assert not hasattr(self.system, object_type.get_plural_name())
        setattr(self.system, object_type.get_plural_name(), binder)

    def __getattr__(self, attr):
        """
        Gets a type binder given its name
        """
        try:
            return self._binders_by_name[attr]
        except LookupError:
            raise AttributeError(attr)

    def __getitem__(self, name):
        """
        Gets a type binder given its name
        """
        if isinstance(name, (str, bytes)):
            return self._binders_by_name[name]
        return self._binders_by_class[name]

    def __dir__(self):
        return dir(type(self)) + list(self.__dict__) + list(self._binders_by_name)

    def __iter__(self):
        return iter(self._binders_by_name.values())

    def __len__(self):
        return len(self._binders_by_name)

    def get_types(self):
        return list(self._binders_by_class)

    def get_binder_by_type_name(self, type_name):
        return self._binders_by_type_name.get(type_name)
