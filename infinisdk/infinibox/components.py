###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from ..core.field import Field
from ..core.bindings import InfiniSDKBinding
from ..core.system_component import SystemComponentsBinder
from ..core.system_object import SystemObject, APICommandFailed
from infi.pyutils.lazy import cached_method
from .component_query import InfiniBoxComponentQuery
from ..core.bindings import ListOfRelatedComponentBinding

from urlobject import URLObject as URL
import gossip


class InfiniBoxSystemComponents(SystemComponentsBinder):

    def __init__(self, system):
        super(InfiniBoxSystemComponents, self).__init__(InfiniBoxSystemComponent, system)
        self.system_component = System(self.system, {'parent_id': "", 'id': 0})
        self.cache_component(self.system_component)
        Rack = self.racks.object_type
        self._rack_1 = Rack(self.system, {'parent_id': self.system_component.id, 'rack': 1})
        self.cache_component(self._rack_1)
        self._fetched_nodes = False
        self._fetched_others = False

    def should_fetch_nodes(self):
        return not self._fetched_nodes

    def should_fetch_all(self):
        return not self._fetched_others

    def mark_fetched_nodes(self):
        self._fetched_nodes = True

    def mark_fetched_all(self):
        self._fetched_others = True
        self._fetched_nodes = True

    def get_rack_1(self):
        return self._rack_1


class ComputedIDBinding(InfiniSDKBinding):

    def get_api_value_from_value(self, system, objtype, obj, value):
        return int(value.rsplit(':', 1)[1])

    def get_value_from_api_object(self, system, objtype, obj, api_obj):
        parent_id = api_obj.get('parent_id', '')
        returned = "{0}_".format(parent_id) if parent_id else ""
        index = objtype.fields.index.binding.get_value_from_api_object(system, objtype, obj, api_obj)
        returned += '{0}:{1}'.format(objtype.get_type_name(), index)
        return returned

    def get_value_from_api_value(self, *args):
        raise NotImplementedError() # pragma: no cover

class InfiniBoxSystemComponent(SystemObject):
    BINDER_CLASS = SystemComponentsBinder
    BASE_URL = URL("components")
    FIELDS = [
        Field("id", binding=ComputedIDBinding(), is_identity=True, cached=True),
        Field("parent_id", cached=True, add_updater=False, is_identity=True),
    ]

    def get_parent(self):
        return self.system.components.try_get_component_by_id(self.get_parent_id())

    @cached_method
    def get_this_url_path(self):
        parent_url = self.get_parent().get_this_url_path()
        this_url = parent_url.add_path(self.get_plural_name()).add_path(str(self.get_index()))
        return this_url

    @classmethod
    def get_url_path(cls, system):
        # Currently there is no url, in infinibox, to get all instances of specific component
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    def get_type_name(cls):
        return cls.__name__.lower()

    @classmethod
    def get_plural_name(cls):
        return "{0}s".format(cls.get_type_name())

    @classmethod
    def find(cls, system, *predicates, **kw):
        return InfiniBoxComponentQuery(system, cls, *predicates, **kw)

    def get_sub_components(self):
        return self.system.components.find(parent_id=self.id)

    def refresh(self):
        data = self.system.api.get(self.get_this_url_path()).get_json()['result']
        self.construct(self.system, data, self.get_parent_id())

    @classmethod
    def construct(cls, system, data, parent_id):
        data['parent_id'] = parent_id
        component_id = cls.fields.id.binding.get_value_from_api_object(system, cls, None, data)
        returned = system.components.try_get_component_by_id(component_id)
        if returned is None:
            component_type = cls.get_type_name()
            object_type = system.components._COMPONENTS_BY_TYPE_NAME.get(component_type, InfiniBoxSystemComponent)
            returned = object_type(system, data)
            system.components.cache_component(returned)
        else:
            returned.update_field_cache(data)
        for field in cls.fields:
            if isinstance(field.binding, ListOfRelatedComponentBinding):
                field.binding.get_value_from_api_object(system, cls, returned, data)
        return returned


@InfiniBoxSystemComponents.install_component_type
class Rack(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="rack", type=int, cached=True),
        Field("enclosures", type=list, binding=ListOfRelatedComponentBinding()),
        Field("nodes", type=list, binding=ListOfRelatedComponentBinding()),
    ]

    @classmethod
    def get_specific_rack_url(cls, rack_id):
        racks_url = cls.BASE_URL.add_path(cls.get_plural_name())
        return racks_url.add_path(str(rack_id))

    @cached_method
    def get_this_url_path(self):
        return self.get_specific_rack_url(self.get_index())


@InfiniBoxSystemComponents.install_component_type
class Enclosure(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, cached=True),
        Field("drives", type=list, binding=ListOfRelatedComponentBinding()),
        Field("state", cached=False),
    ]


@InfiniBoxSystemComponents.install_component_type
class Node(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, cached=True),
        Field("name"),
        Field("fc_ports", type=list, binding=ListOfRelatedComponentBinding()),
        Field("eth_ports", type=list, binding=ListOfRelatedComponentBinding()),
        Field("drives", type=list, binding=ListOfRelatedComponentBinding("local_drives")),
        Field("services", type=list, binding=ListOfRelatedComponentBinding()),
        Field("state", cached=False),
    ]

    @classmethod
    def get_url_path(cls, system):
        return cls.BASE_URL.add_path(cls.get_plural_name())

    def phase_out(self):
        hook_tags = ['infinibox', 'node_{0}'.format(self.get_index())]
        gossip.trigger_with_tags('infinidat.infinibox.pre_node_phase_out', {'node': self}, tags=hook_tags)
        try:
            res = self.system.api.post(self.get_this_url_path().add_path('phase_out'))
        except APICommandFailed as e:
            gossip.trigger_with_tags('infinidat.infinibox.node_phase_out_failure', {'node': self, 'exc': e}, tags=hook_tags)
            raise
        gossip.trigger_with_tags('infinidat.infinibox.post_node_phase_out', {'node': self}, tags=hook_tags)
        return res

    def phase_in(self):
        hook_tags = ['infinibox', 'node_{0}'.format(self.get_index())]
        gossip.trigger_with_tags('infinidat.infinibox.pre_node_phase_in', {'node': self}, tags=hook_tags)
        try:
            res = self.system.api.post(self.get_this_url_path().add_path('phase_in'))
        except APICommandFailed as e:
            gossip.trigger_with_tags('infinidat.infinibox.node_phase_in_failure', {'node': self, 'exc': e}, tags=hook_tags)
            raise
        gossip.trigger_with_tags('infinidat.infinibox.post_node_phase_in', {'node': self}, tags=hook_tags)
        return res

    def __repr__(self):
        return '<Node {0}>'.format(self.get_index())

@InfiniBoxSystemComponents.install_component_type
class LocalDrive(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="drive_index", type=int, cached=True),
        Field("model"),
        Field("vendor"),
        Field("firmware"),
        Field("state", cached=False),
        Field("type"),
        Field("serial_number"),
    ]

    @classmethod
    def get_type_name(cls):
        return "local_drive"

    def is_ssd(self):
        return self.get_type() == 'SSD'

@InfiniBoxSystemComponents.install_component_type
class EthPort(InfiniBoxSystemComponent):
    FIELDS = [
        Field("hw_addr", is_identity=True),
        Field("connection_speed"),
        Field("device_name", api_name="name"),
        Field("port_number", type=int, cached=True),
        Field("index", api_name="id", type=int, cached=True),
        Field("node", api_name="node_index", type=int, cached=True),
        Field("role", cached=True),
        Field("system_interface_port_number", type=int),
        Field("state", cached=False),
        Field("ip_v4_addr"),
        Field("ip_v4_broadcast"),
        Field("ip_v4_netmask"),
        Field("ip_v6_addr"),
        Field("ip_v6_netmask"),
    ]

    @classmethod
    def get_type_name(cls):
        return "eth_port"

@InfiniBoxSystemComponents.install_component_type
class FcPort(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, cached=True),
        Field("wwpn", is_identity=True),
        Field("node", cached=True),
        Field("state", cached=False),
        Field("link_state", cached=False),
    ]

    @classmethod
    def get_type_name(cls):
        return "fc_port"

@InfiniBoxSystemComponents.install_component_type
class Drive(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="drive_index", type=int, is_identity=True, cached=True),
        Field("enclosure_index", type=int, cached=True),
        Field("serial_number"),
        Field("state", cached=False),
    ]

@InfiniBoxSystemComponents.install_component_type
class Service(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="name", cached=True),
        Field("name", is_identity=True, cached=True),
        Field("state", cached=False),
    ]

    def get_service_cluster(self):
        return self.system.components.service_clusters.get(name=self.get_name())

    def start(self):
        self.get_service_cluster().start(node=self.get_parent())

    def stop(self):
        self.get_service_cluster().stop(node=self.get_parent())

@InfiniBoxSystemComponents.install_component_type
class ServiceCluster(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="name", cached=True),
        Field("name", is_identity=True, cached=True),
        Field("state", api_name="cluster_state", cached=False),
        ]

    @classmethod
    def get_type_name(cls):
        return "service_cluster"

    @classmethod
    def get_url_path(cls, system):
        return URL('services')

    @cached_method
    def get_this_url_path(self):
        services_url = self.get_url_path(self.system)
        this_url = services_url.add_path(str(self.get_index()))
        return this_url

    def start(self, node=None):
        data = {'node_id': node.id} if node else None
        self.system.api.post(self.get_this_url_path().add_path('start'), data=data)

    def stop(self, node=None):
        data = {'node_id': node.id} if node else None
        self.system.api.post(self.get_this_url_path().add_path('stop'), data=data)

@InfiniBoxSystemComponents.install_component_type
class System(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, cached=True),
        Field("state", add_getter=False, cached=False),
    ]

    @cached_method
    def get_this_url_path(self):
        return URL('system')

    def get_state(self):
        return self.get_field('operational_state')['state']
