from ..core import Field
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject
from ..core.bindings import ListToDictBinding, RelatedComponentBinding, RelatedObjectBinding


class NetworkInterface(InfiniBoxObject):
    URL_PATH = 'network/interfaces'

    FIELDS = [
        Field("id", is_identity=True, type=int, is_filterable=True, is_sortable=True, cached=True),
        Field("ports", optional=True, creation_parameter=True, mutable=True, type=list, add_updater=False,
              binding=ListToDictBinding(key="name")),
        Field("node", api_name="node_id", type=int, creation_parameter=True, use_in_repr=True, mutable=False,
              is_sortable=True, binding=RelatedComponentBinding(), optional=True),
        Field("state", cached=False),
        Field("type", creation_parameter=True, default="PORT_GROUP"),
        Field("rate_limit", type=int, mutable=True, creation_parameter=True, optional=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("pg_{ordinal}")),
        Field("underlying_interface", api_name="underlying_interface_id", type=int, creation_parameter=True,
              binding=RelatedObjectBinding(collection_name="network_interfaces"), cached=True, optional=True),
        Field("vlan", type=int, creation_parameter=True, optional=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_network_configuration()

    @classmethod
    def get_type_name(cls):
        return 'network_interface'

    def get_network_spaces(self):
        return [network_space
                for network_space in self.system.network_spaces
                if self in network_space.get_interfaces()]

    def add_port(self, port):
        url = self.get_this_url_path().add_path("ports")
        data = self.fields.ports.binding.get_api_value_from_value(None, None, None, [port])[0]
        return self.system.api.post(url, data=data).get_result()

    def remove_port(self, port):
        url = self.get_this_url_path().add_path("ports").add_path("{}".format(port))
        return self.system.api.delete(url).get_result()

    def disable(self):
        url = self.get_this_url_path().add_path("disable")
        return self.system.api.post(url)

    def enable(self):
        url = self.get_this_url_path().add_path("enable")
        return self.system.api.post(url)

    def is_enabled(self):
        return self.get_state() in ['OK', 'ENABLED']

    def is_vlan(self):
        return self.get_type() == 'VLAN'
