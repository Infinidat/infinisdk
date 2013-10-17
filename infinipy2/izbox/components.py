from ..core.field import Field
from ..core.system_component import SystemComponentsBinder
from ..core.system_object import SystemObject

from infi.pyutils.lazy import cached_method

from urlobject import URLObject as URL

class IZBoxSystemComponents(SystemComponentsBinder):

    def __init__(self, system):
        super(IZBoxSystemComponents, self).__init__(IZBoxSystemComponent, system)
        self.system_component = System(self.system, {"type": "system", "id": 0})
        self.cache_component(self.system_component)

class IZBoxSystemComponent(SystemObject):
    BINDER_CLASS = SystemComponentsBinder

    FIELDS = [
        Field("id", type=int),
        Field("status"),
        Field("index", type=int),
        Field("parent_index", type=int),
    ]

    @cached_method
    def get_this_url_path(self):
        return super(IZBoxSystemComponent, self).get_this_url_path().del_query_param("type")

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
            object_type = system.components._COMPONENTS_BY_TYPE_NAME.get(component_type, IZBoxSystemComponent)
            returned = object_type(system, data)
            system.components.cache_component(returned)
        return returned

@IZBoxSystemComponents.install_component_type
class Enclosure(IZBoxSystemComponent):
    pass

@IZBoxSystemComponents.install_component_type
class Node(IZBoxSystemComponent):

    def is_primary(self):
        return self is self.system.components.system_component.get_primary_node()

@IZBoxSystemComponents.install_component_type
class System(IZBoxSystemComponent):

    def get_primary_node(self):
        return self.system.components.nodes.get(index=self.get_primary_node_index())

    def get_primary_node_index(self, use_cache=False):
        return self.get_field("data", use_cache)["primary_node_id"]

    def get_secondary_node(self):
        return self.system.components.nodes.get(index=self.get_secondary_node_index())

    def get_secondary_node_index(self, use_cache=False):
        return 1 if self.get_primary_node_index() == 2 else 2

