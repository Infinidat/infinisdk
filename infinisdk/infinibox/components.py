
from .._compat import ExitStack, zip
from ..core.field import Field
from ..core.utils import deprecated
from ..core.system_component import SystemComponentsBinder
from ..core.system_object import SystemObject
from ..core.exceptions import ObjectNotFound
from ..core.type_binder import TypeBinder
from ..core.translators_and_types import WWNType
from infi.pyutils.lazy import cached_method
from .component_query import InfiniBoxComponentQuery
from ..core.bindings import InfiniSDKBinding, ListOfRelatedComponentBinding, RelatedComponentBinding

from collections import defaultdict
from contextlib import contextmanager
from logbook import Logger
from pact import Pact
from urlobject import URLObject as URL

_logger = Logger(__name__)


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
        self._fetched_service_clusters = False
        self._deps_by_compoents_tree = defaultdict(set)

    def get_depended_components_type(self, component_type):
        deps = self._deps_by_compoents_tree[component_type].copy()
        for dep_type in deps.copy():
            deps.update(self.get_depended_components_type(dep_type))
        return deps

    def should_fetch_nodes(self):
        return not self._fetched_nodes

    def should_fetch_all(self):
        return not self._fetched_others

    def should_fetch_service_clusters(self):
        return not self._fetched_service_clusters


    def mark_fetched_nodes(self):
        self._fetched_nodes = True

    def mark_fetched_all(self):
        self._fetched_others = True
        self._fetched_nodes = True

    def mark_fetched_service_clusters(self):
        self._fetched_service_clusters = True

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


class NotExistsSupportBinding(InfiniSDKBinding):
    # Prior to 2.0 not all services have all the fields. For now, return None if missing.
    # TODO: Check that system version <= 1.7
    def __init__(self, value_for_non_exists=None):
        super(NotExistsSupportBinding, self).__init__()
        self._value_for_non_exists = value_for_non_exists
        pass

    def get_value_from_api_object(self, system, objtype, obj, api_obj):
        try:
            return super(NotExistsSupportBinding, self).get_value_from_api_object(system, objtype, obj, api_obj)
        except KeyError:
            return self._value_for_non_exists


class InfiniBoxComponentBinder(TypeBinder):

    _force_fetching_from_cache = False

    def should_force_fetching_from_cache(self):
        return self._force_fetching_from_cache

    def get_by_id_lazy(self, id):
        returned = self.safe_get_by_id(id)
        if returned is None:
            raise NotImplementedError("Initializing infinibox components lazily is not yet supported") # pragma: no cover
        return returned

    @contextmanager
    def force_fetching_from_cache_context(self):
        prev = self._force_fetching_from_cache
        self._force_fetching_from_cache = True
        try:
            yield
        finally:
            self._force_fetching_from_cache = prev

    @contextmanager
    def _force_fetching_tree_from_cache_context(self):
        with ExitStack() as stack:
            stack.enter_context(self.force_fetching_from_cache_context())
            for obj_type in self.system.components.get_depended_components_type(self.object_type):
                obj_collection = self.system.components[obj_type]
                stack.enter_context(obj_collection.force_fetching_from_cache_context())
            yield

    @deprecated(message='Use fetch_tree_once_context instead')
    def fetch_once_context(self):
        return self.fetch_tree_once_context()

    @contextmanager
    def fetch_tree_once_context(self, force_fetch=True, with_logging=True):
        is_forced_cache = self.should_force_fetching_from_cache()
        if not is_forced_cache:
            if with_logging:
                _logger.debug('Entering fetch tree once of {0}', self)
            self._fetch_tree(force_fetch)
        with self._force_fetching_tree_from_cache_context():
            yield
        if not is_forced_cache and with_logging:
            _logger.debug('Exiting fetch tree once of {0}', self)


    def _fetch_tree(self, force_fetch):
        components = self.system.components
        if self.object_type in [
                components.nodes.object_type,
                components.services.object_type,
                components.fc_ports.object_type,
                components.eth_ports.object_type,
                components.local_drives.object_type,
                ]:
            if force_fetch or components.should_fetch_nodes():
                rack_1 = components.get_rack_1()
                rack_1.refresh_without_enclosures()
        elif self.object_type is components.service_clusters.object_type:
            if force_fetch or components.should_fetch_service_clusters():
                self._fetch_service_clusters()
        else:
            if force_fetch or components.should_fetch_all():
                rack_1 = components.get_rack_1()
                rack_1.refresh()

    def _fetch_service_clusters(self):
        components = self.system.components
        service_cluster_type = components.service_clusters.object_type
        url = service_cluster_type.get_url_path(self.system)
        clusters_data = self.system.api.get(url).get_result()
        components.mark_fetched_service_clusters()
        for cluster_data in clusters_data:
            service_cluster_type.construct(self.system, cluster_data, None)


class InfiniBoxSystemComponent(SystemObject):
    BINDER_CLASS = InfiniBoxComponentBinder
    BASE_URL = URL("components")
    FIELDS = [
        Field("id", binding=ComputedIDBinding(), is_identity=True, cached=True),
        Field("parent_id", cached=True, add_updater=False, is_identity=True),
    ]

    def _deduce_from_cache(self, *args, **kwargs):
        collection = self.system.components[self.get_plural_name()]
        if collection.should_force_fetching_from_cache():
            return True
        return super(InfiniBoxSystemComponent, self)._deduce_from_cache(*args, **kwargs)

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
        data = self.system.api.get(self.get_this_url_path()).get_result()
        self.construct(self.system, data, self.get_parent_id())

    @classmethod
    def construct(cls, system, data, parent_id, allow_partial_fields=False):
        data['parent_id'] = parent_id
        component_id = cls.fields.id.binding.get_value_from_api_object(system, cls, None, data)
        returned = system.components.try_get_component_by_id(component_id)
        if returned is None:
            component_type = cls.get_type_name()
            object_type = system.components._COMPONENTS_BY_TYPE_NAME.get(component_type, InfiniBoxSystemComponent)
            returned = object_type(system, data)
            system.components._deps_by_compoents_tree[type(returned.get_parent())].add(object_type)
            system.components.cache_component(returned)
        else:
            returned.update_field_cache(data)
        for field in cls.fields:
            if isinstance(field.binding, ListOfRelatedComponentBinding):
                try:
                    field.binding.get_value_from_api_object(system, cls, returned, data)
                except KeyError:
                    if not allow_partial_fields:
                        raise
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

    def refresh_without_enclosures(self):
        url = self.get_this_url_path().add_query_param('fields','enclosures_number,rack,nodes')
        self.system.components.mark_fetched_nodes()
        data = self.system.api.get(url).get_result()
        data['enclosures'] = []
        self.construct(self.system, data, self.get_parent_id())

    def refresh(self):
        self.system.components.mark_fetched_all()
        super(Rack, self).refresh()


@InfiniBoxSystemComponents.install_component_type
class Enclosure(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, cached=True),
        Field("drives", type=list, binding=ListOfRelatedComponentBinding()),
        Field("state", cached=False),
    ]


class Nodes(InfiniBoxComponentBinder):

    def get_by_wwpn(self, wwpn):
        return self.system.components.fc_ports.get(wwpn=wwpn).get_node()

    def refresh_fields(self, field_names):
        assert isinstance(field_names, (list, tuple)), "field_names must be either a list or a tuple"
        field_names_str = ",".join(set(field_names).union(['id']))
        url = self.object_type.get_url_path(self.system).set_query_param('fields', field_names_str)
        data = self.system.api.get(url).get_result()
        parent_id = self.system.components.get_rack_1().get_id()
        return [self.object_type.construct(self.system, obj_data, parent_id, True) for obj_data in data]


@InfiniBoxSystemComponents.install_component_type
class Node(InfiniBoxSystemComponent):
    BINDER_CLASS = Nodes
    FIELDS = [
        Field("index", api_name="id", type=int, cached=True),
        Field("name", cached=True),
        Field("fc_ports", type=list, binding=ListOfRelatedComponentBinding()),
        Field("eth_ports", type=list, binding=ListOfRelatedComponentBinding()),
        Field("drives", type=list, binding=ListOfRelatedComponentBinding("local_drives")),
        Field("services", type=list, binding=ListOfRelatedComponentBinding()),
        Field("state", cached=False),
    ]

    def is_active(self):
        return self.get_state() == 'ACTIVE'

    def is_degraded(self):
        return self.get_state() == 'DEGRADED'

    def is_failed(self):
        return self.get_state() == 'FAILED'

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

    def _get_tags(self):
        return ['infinibox', 'node{0}'.format(self.get_index())]

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

    def is_active(self):
        return self.get_state() == 'OK'

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
        Field("name", cached=True),
        Field("system_interface_port_number", type=int),
        Field("state", cached=False),
        Field("link_state", cached=False, binding=NotExistsSupportBinding()),
        Field("ip_v4_addr"),
        Field("ip_v4_broadcast"),
        Field("ip_v4_netmask"),
        Field("ip_v6_addr"),
        Field("ip_v6_netmask"),
    ]

    @classmethod
    def get_type_name(cls):
        return "eth_port"

    def is_link_up(self):
        if self.get_state() != 'OK':
            return False
        return self.get_link_state().lower() in ("link up", "up")


class FcPorts(InfiniBoxComponentBinder):
    def get_online_target_addresses(self):
        addresses = []
        with self.fetch_tree_once_context():
            for fc_port in self:
                if fc_port.is_link_up():
                    addresses.extend(fc_port.get_target_addresses())
        return addresses

@InfiniBoxSystemComponents.install_component_type
class FcPort(InfiniBoxSystemComponent):
    BINDER_CLASS = FcPorts
    FIELDS = [
        Field("index", api_name="id", type=int, cached=True),
        Field("wwpn", is_identity=True, cached=True, type=WWNType),
        Field("node", api_name="node_index", type=int, cached=True, binding=RelatedComponentBinding()),
        Field("state", cached=False),
        Field("link_state", cached=False),
        Field("role", cached=True),
        Field("soft_target_addresses", type=list, cached=True),
        Field("switch_vendor", cached=True),
        Field("enabled", type=bool, binding=NotExistsSupportBinding(True)),
    ]

    def is_link_up(self):
        if not self.is_enabled():
            return False
        if self.get_state() != 'OK':
            return False
        return self.get_link_state().lower() in ("link up", "up")

    @classmethod
    def get_type_name(cls):
        return "fc_port"

    def is_hard_port(self):
        if self.system.compat.has_npiv():
            return self.get_role() == 'HARD_PORT'
        return True

    def is_soft_port(self):
        if self.system.compat.has_npiv():
            return self.get_role() == 'SOFT_PORT'
        return False

    def get_target_addresses(self):
        if self.is_soft_port():
            return self.get_soft_target_addresses()
        return set([self.get_wwpn()])

@InfiniBoxSystemComponents.install_component_type
class Drive(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="drive_index", type=int, is_identity=True, cached=True),
        Field("enclosure_index", type=int, cached=True),
        Field("enclosure", api_name="enclosure_index", type=int, cached=True, binding=RelatedComponentBinding()),
        Field("serial_number"),
        Field("state", cached=False),
    ]

    def get_paths(self, from_cache=False):
        node_access_flags = self.get_field('nodes_access', from_cache=from_cache)
        return [node
                for node, can_access_node in zip(self.system.components.nodes, node_access_flags)
                if can_access_node]

    def is_active(self):
        return self.get_state() == 'ACTIVE'

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
        return self.get_service_cluster().start(node=self.get_parent())

    def stop(self):
        return self.get_service_cluster().stop(node=self.get_parent())

    def is_active(self):
        return self.get_state() == 'ACTIVE'

    def is_inactive(self):
        return self.get_state() == 'INACTIVE'

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
        if node:
            data = {'node_id': node.get_index()}
            obj = node.get_service(self.get_name())
        else:
            data = {}
            obj = self
        pact = Pact('Starting {0}'.format(obj)).until(obj.is_active)
        self.system.api.post(self.get_this_url_path().add_path('start'), data=data)
        return pact

    def stop(self, node=None):
        if node:
            data = {'node_id': node.get_index()}
            obj = node.get_service(self.get_name())
        else:
            data = {}
            obj = self
        pact = Pact('Stopping {0}'.format(obj)).until(obj.is_inactive)
        self.system.api.post(self.get_this_url_path().add_path('stop'), data=data)
        return pact

    def is_active(self):
        return self.get_state() == 'ACTIVE'

    def is_inactive(self):
        return self.get_state() == 'INACTIVE'

@InfiniBoxSystemComponents.install_component_type
class System(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, cached=True),
        Field("operational_state", type=dict, cached=False),
    ]

    @cached_method
    def get_this_url_path(self):
        return URL('system')

    def get_state(self, *args, **kwargs):
        return self.get_operational_state(*args, **kwargs)['state']

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

    def refresh(self):
        data = self.system.api.get(self.get_this_url_path()).get_result()
        self.update_field_cache(data)
