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
from ..core.system_component import SystemComponentsBinder
from ..core.system_object import SystemObject, APICommandFailed, ObjectNotFound
from ..core.type_binder import TypeBinder
from infi.pyutils.lazy import cached_method
from .component_query import InfiniBoxComponentQuery
from ..core.bindings import InfiniSDKBinding, ListOfRelatedComponentBinding, RelatedComponentBinding

from urlobject import URLObject as URL
import gossip
from pact import Pact
import sentinels


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

class InfiniBoxComponentBinder(TypeBinder):
    def get_by_id_lazy(self, id):
        returned = self.safe_get_by_id(id)
        if returned is None:
            raise NotImplementedError("Initializing infinibox components lazily is not yet supported") # pragma: no cover
        return returned

class InfiniBoxSystemComponent(SystemObject):
    BINDER_CLASS = InfiniBoxComponentBinder
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

    def is_active(self):
        return self.get_state() == 'ACTIVE'

    @classmethod
    def get_url_path(cls, system):
        return cls.BASE_URL.add_path(cls.get_plural_name())

    def get_service(self, service_name):
        """Get a service object by its type name

        :param service_name: the service name (mgmt/core/etc.)
        """
        return self.system.components.services.get(parent_id=self.id, name=service_name)

    def get_management_service(self):
        """Gets the management service running on this node
        """
        return self.get_service('mgmt')

    def get_core_service(self):
        """Gets the core service running on this node
        """
        return self.get_service('core')

    def phase_out(self):
        gossip.trigger_with_tags('infinidat.sdk.pre_node_phase_out', {'node': self}, tags=self._get_tags())

        try:
            with self.system.cluster.possible_management_take_over_context(self):
                self.system.api.post(self.get_this_url_path().add_path('phase_out'))
        except APICommandFailed as e:
            gossip.trigger_with_tags('infinidat.sdk.node_phase_out_failure', {'node': self, 'exc': e},
                                     tags=self._get_tags())
            raise
        gossip.trigger_with_tags('infinidat.sdk.post_node_phase_out', {'node': self}, tags=self._get_tags())
        return Pact('phase out {0}'.format(self)).until(lambda: self.get_state() == 'READY')

    def _get_tags(self):
        return ['infinibox', 'node{0}'.format(self.get_index())]

    def _notify_phased_in(self):
        gossip.trigger_with_tags('infinidat.sdk.node_phased_in', {'node': self}, tags=self._get_tags())

    def phase_in(self):
        gossip.trigger_with_tags('infinidat.sdk.pre_node_phase_in', {'node': self}, tags=self._get_tags())
        try:
            self.system.api.post(self.get_this_url_path().add_path('phase_in'))
        except APICommandFailed as e:
            gossip.trigger_with_tags('infinidat.sdk.node_phase_in_failure', {'node': self, 'exc': e},
                                     tags=self._get_tags())
            raise
        gossip.trigger_with_tags('infinidat.sdk.post_node_phase_in', {'node': self}, tags=self._get_tags())
        return Pact('phase in {0}'.format(self)).until(self.is_active).then(self._notify_phased_in)

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
        Field("node", api_name="node_index", type=int, cached=True, binding=RelatedComponentBinding()),
    ]

    @classmethod
    def get_type_name(cls):
        return "local_drive"

    @cached_method
    def get_this_url_path(self):
        parent_url = self.get_parent().get_this_url_path()
        this_url = parent_url.add_path("drives").add_path(str(self.get_index()))
        return this_url

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
        Field("node", api_name="node_index", type=int, cached=True, binding=RelatedComponentBinding()),
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
        Field("node", api_name="node_index", type=int, cached=True, binding=RelatedComponentBinding()),
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
        Field("enclosure", api_name="enclosure_index", type=int, cached=True, binding=RelatedComponentBinding()),
        Field("serial_number"),
        Field("state", cached=False),
    ]

FIELD_NOT_EXISTS = sentinels.Sentinel('FIELD_NOT_EXISTS')

class NotExistsSupportBinding(InfiniSDKBinding):
    # INFINIBOX-12634: Workaround until all services would have the same fields
    def get_value_from_api_object(self, system, objtype, obj, api_obj):
        try:
            return super(NotExistsSupportBinding, self).get_value_from_api_object(system, objtype, obj, api_obj)
        except KeyError:
            return FIELD_NOT_EXISTS

@InfiniBoxSystemComponents.install_component_type
class Service(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="name", cached=True),
        Field("name", is_identity=True, cached=True),
        Field("role", binding=NotExistsSupportBinding(), cached=False),
        Field("state", cached=False),
    ]

    def get_service_cluster(self):
        try:
            return self.system.components.service_clusters.get(name=self.get_name())
        except ObjectNotFound:
            raise NotImplementedError("This service ({0}) doesn't support CLM".format(self.get_name()))

    def start(self):
        self.get_service_cluster().start(node=self.get_parent())

    def stop(self):
        self.get_service_cluster().stop(node=self.get_parent())

    def is_active(self):
        return self.get_state() == 'ACTIVE'

    def is_master(self):
        return self.get_role() == 'MASTER'

    def is_secondary(self):
        return self.get_role() == 'SECONDARY'

    def is_member(self):
        return self.get_role() == 'MEMBER'

    def get_node(self):
        return self.get_parent()

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

    def get_services(self):
        return [self.system.components.nodes.get(index=service_info['node_id']).get_service(self.get_name())
                for service_info in self.get_field('node_states')]

    def start(self, node=None):
        data = {'node_id': node.get_index()} if node else {}
        self.system.api.post(self.get_this_url_path().add_path('start'), data=data)

    def stop(self, node=None):
        data = {'node_id': node.get_index()} if node else {}
        self.system.api.post(self.get_this_url_path().add_path('stop'), data=data)

    def is_active(self):
        return self.get_state() == 'ACTIVE'

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

    def safe_get_state(self):
        try:
            return self.get_state()
        except:
            return None

    def is_active(self):
        return self.safe_get_state() == 'ACTIVE'

    def is_stand_by(self):
        return self.safe_get_state() == 'STANDBY'

    def is_down(self):
        return self.safe_get_state() is None
