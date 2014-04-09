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

    @cached_method
    def get_alert_types(self):
        return self.system.api.get("components/alerts").get_result()

    @cached_method
    def get_type_infos_from_system(self):
        return self.system.api.get("components/types").get_result()

class IZBoxSystemComponent(SystemObject):
    BINDER_CLASS = SystemComponentsBinder

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("type", is_identity=True),
        Field("status"),
        Field("state"),
        Field("index", type=int, cached=True),
        Field("parent_index", type=int, cached=True),
        Field("parent_id", type=int, cached=True),
        Field("alerts", type=list),
        Field("data", type=dict),
    ]

    def is_ok(self):
        return self.get_status().lower() == "ok"

    def get_additional_data(self):
        return self.get_field("data", from_cache=True)

    def get_parent(self):
        return self.system.components.get_by_id_lazy(self.get_parent_id())

    def get_sub_components(self):
        return self.system.components.find(parent_id=self.id)

    @cached_method
    def get_this_url_path(self):
        return super(IZBoxSystemComponent, self).get_this_url_path().del_query_param("type")

    @classmethod
    def get_url_path(cls, system):
        returned = URL("/api/rest/components")
        if cls is not system.components.object_type:
            returned = returned.add_query_param("type", "eq:{0}".format(cls.get_type_name()))
        return returned

    @classmethod
    def get_type_name(cls):
        return cls.__name__.lower()

    @classmethod
    def construct(cls, system, data):
        component_id = data["id"]
        returned = system.components.try_get_component_by_id(component_id)
        if returned is None:
            component_type = data["type"]
            object_type = system.components._COMPONENTS_BY_TYPE_NAME.get(component_type, IZBoxSystemComponent)
            returned = object_type(system, data)
            system.components.cache_component(returned)
        else:
            returned.update_field_cache(data)
        return returned

@IZBoxSystemComponents.install_component_type
class Rack(IZBoxSystemComponent):
    pass

@IZBoxSystemComponents.install_component_type
class Enclosure(IZBoxSystemComponent):
    pass

@IZBoxSystemComponents.install_component_type
class Node(IZBoxSystemComponent):

    def get_address(self):
        return ("{0}-{1}".format(self.system.get_name(), self.get_index()))

    def is_primary(self):
        return self is self.system.components.system_component.get_primary_node()

    def is_secondary(self):
        return not self.is_primary()

@IZBoxSystemComponents.install_component_type
class NodeEthPort(IZBoxSystemComponent):

    @classmethod
    def get_type_name(self):
        return "node_eth_port"

    @classmethod
    def get_plural_name(self):
        return "{0}s".format(self.get_type_name())


@IZBoxSystemComponents.install_component_type
class EnclosureDrive(IZBoxSystemComponent):

    @classmethod
    def get_type_name(self):
        return "enclosure_drive"

    @classmethod
    def get_plural_name(self):
        return "{0}s".format(self.get_type_name())

    def get_designated_role(self):
        return self.get_data()['designated_role']
    def phasein(self):
        self.system.api.post("{0}/phasein".format(self.get_this_url_path()))
    def phaseout(self):
        self.system.api.post("{0}/phaseout".format(self.get_this_url_path()))

@IZBoxSystemComponents.install_component_type
class Service(IZBoxSystemComponent):

    def get_name(self):
        return self.get_additional_data()["name"]


@IZBoxSystemComponents.install_component_type
class System(IZBoxSystemComponent):

    def get_primary_node(self):
        return self.system.components.nodes.get(index=self.get_primary_node_index())

    def get_primary_node_index(self, use_cache=False):
        return self.get_field("data", from_cache=use_cache, fetch_if_not_cached=True)["primary_node_id"]

    def get_secondary_node(self):
        return self.system.components.nodes.get(index=self.get_secondary_node_index())

    def get_secondary_node_index(self, use_cache=False):
        return 1 if self.get_primary_node_index(use_cache) == 2 else 2

    def get_state(self):
        return self.get_field("data")["system_state"]
