from .._compat import itervalues
from .field import Field
from .system_object import SystemObject
from .type_binder import TypeBinder
from urlobject import URLObject as URL

class SystemComponentsBinder(TypeBinder):

    class types:
        pass

    def __init__(self, system):
        super(SystemComponentsBinder, self).__init__(SystemComponent, system)
        self._components_by_id = {}

    def get_component_types(self):
        """
        Returns all classes installed for specific component types
        """
        return list(itervalues(_COMPONENTS_BY_TYPE_NAME))

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

    def get_by_id_lazy(self, id):
        returned = self.try_get_component_by_id(id)
        if returned is None:
            raise NotImplementedError("Initializing generic components lazily is not yet supported") # pragma: no cover
        return returned

_COMPONENTS_BY_TYPE_NAME = {}

def _make_component_type(object_type):
    setattr(SystemComponentsBinder, object_type.get_plural_name(), SpecificComponentBinderGetter(object_type))
    _COMPONENTS_BY_TYPE_NAME[object_type.get_type_name()] = object_type
    setattr(SystemComponentsBinder.types, object_type.__name__, object_type)
    return object_type

class SpecificComponentBinderGetter(object):

    def __init__(self, object_type):
        super(SpecificComponentBinderGetter, self).__init__()
        self.object_type = object_type
        self.cached_name = "_cached__{}".format(self.object_type.get_plural_name())

    def __get__(self, components_binder, _):
        returned = getattr(components_binder, self.cached_name, None)
        if returned is None:
            returned = SpecificComponentBinder(self.object_type, components_binder.system)
            setattr(components_binder, self.cached_name, returned)
        return returned

class SpecificComponentBinder(TypeBinder):

    def get_by_id_lazy(self, id):
        returned = self.system.components.try_get_component_by_id(id)
        if returned is None:
            returned = self.object_type(self.system, {"id": id, "type": self.object_type.get_type_name()})
            self.system.components.cache_component(returned)
        return returned

class SystemComponent(SystemObject):
    BINDER_CLASS = SystemComponentsBinder

    FIELDS = [
        Field("id", type=int),
        Field("status"),
    ]

    @classmethod
    def get_url_path(cls, system):
        return URL("/api/rest/components").add_query_param("type", "eq:{}".format(cls.get_type_name()))

    @classmethod
    def get_type_name(cls):
        return cls.__name__.lower()

    @classmethod
    def construct(cls, system, data):
        component_id = data["id"]
        component_type = data["type"]
        returned = system.components.try_get_component_by_id(component_id)
        if returned is None:
            object_type = _COMPONENTS_BY_TYPE_NAME.get(component_type, SystemComponent)
            returned = object_type(system, data)
            system.components.cache_component(returned)
        return returned

@_make_component_type
class Enclosure(SystemComponent):
    pass

@_make_component_type
class System(SystemComponent):
    pass
