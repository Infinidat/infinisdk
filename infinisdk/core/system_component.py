from collections import OrderedDict
from .type_binder import TypeBinder


class SystemComponentsBinder(TypeBinder):

    _COMPONENTS_BY_TYPE_NAME = None
    types = None

    def __init__(self, base_component_type, system):
        super(SystemComponentsBinder, self).__init__(base_component_type, system)
        self._components_by_id = OrderedDict()

    def invalidate_cache(self):
        for component in self._components_by_id.values():
            component.invalidate_cache()

    def get_component_types(self):
        """
        Returns all classes installed for specific component types
        """
        return list(self._COMPONENTS_BY_TYPE_NAME.values())

    def get_component_type_names(self):
        return list(self._COMPONENTS_BY_TYPE_NAME.keys())

    def try_get_component_by_id(self, component_id):
        """
        Returns a cached component by its id, or None if it isn't known yet
        """
        return self._components_by_id.get(component_id, None)

    def cache_component(self, component):
        """
        .. warning:: for internal use only. Don't call this method directly
        """
        self._components_by_id[component.id] = component

    def get_by_id_lazy(self, id):  # pylint: disable=redefined-builtin
        returned = self.try_get_component_by_id(id)
        if returned is None:
            raise NotImplementedError("Initializing generic components lazily is not yet supported") # pragma: no cover
        return returned

    @classmethod
    def install_component_type(cls, component_type):
        setattr(cls, component_type.get_plural_name(), SpecificComponentBinderGetter(component_type))

        if cls._COMPONENTS_BY_TYPE_NAME is None:
            cls._COMPONENTS_BY_TYPE_NAME = {}
        cls._COMPONENTS_BY_TYPE_NAME[component_type.get_type_name()] = component_type  # pylint: disable=unsupported-assignment-operation
        if cls.types is None:
            cls.types = TypeContainer()
        cls.types.install(component_type)
        return component_type

    def __getitem__(self, attr):
        if isinstance(attr, type):
            return self[attr.get_plural_name()]
        try:
            return getattr(self, attr)
        except AttributeError:
            raise KeyError(attr)


class SpecificComponentBinderGetter:

    def __init__(self, object_type):
        super(SpecificComponentBinderGetter, self).__init__()
        self.object_type = object_type
        self.cached_name = "_cached__{}".format(self.object_type.get_plural_name())

    def __get__(self, components_binder, _):
        returned = getattr(components_binder, self.cached_name, None)
        if returned is None:
            returned = self.object_type.bind(components_binder.system)
            setattr(components_binder, self.cached_name, returned)
        return returned


class SpecificComponentBinder(TypeBinder):

    def get_by_id_lazy(self, id):  # pylint: disable=redefined-builtin
        returned = self.system.components.try_get_component_by_id(id)
        if returned is None:
            returned = self.object_type(self.system, {"id": id, "type": self.object_type.get_type_name()})
            self.system.components.cache_component(returned)
        return returned


class TypeContainer:
    def __init__(self):
        super(TypeContainer, self).__init__()
        self._type_name_to_class = {}

    def install(self, component_type):
        type_name = component_type.__name__
        self._type_name_to_class[type_name] = component_type
        setattr(self, type_name, component_type)

    def get_names(self):
        return list(self._type_name_to_class)

    def get_type_by_name(self, name):
        return self._type_name_to_class[name]

    def to_list(self):
        return list(self)

    def __iter__(self):
        return iter(self._type_name_to_class.values())

    def __len__(self):
        return len(self._type_name_to_class)
