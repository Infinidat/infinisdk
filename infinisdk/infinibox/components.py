import copy
import uuid

from ..core.field import Field
from ..core.field_filter import FieldFilter
from ..core.system_component import SystemComponentsBinder
from ..core.system_object import BaseSystemObject
from ..core.exceptions import ObjectNotFound
from ..core.type_binder import MonomorphicBinder
from ..core.translators_and_types import WWNType, CapacityType, MunchType, MunchListType
from mitba import cached_method
from .component_query import InfiniBoxComponentQuery, InfiniBoxGenericComponentQuery
from ..core.bindings import InfiniSDKBinding, ListOfRelatedComponentBinding, RelatedComponentBinding

from collections import defaultdict
from contextlib import contextmanager, ExitStack
from logbook import Logger
from urlobject import URLObject as URL
from vintage import deprecated, warn_deprecation

# pylint: disable=attribute-defined-outside-init,no-member,super-on-old-class,no-init,abstract-method
_logger = Logger(__name__)
_UID_DEPRECATION_MSG = "Direct usage of the 'id' field is deprecated. Use 'uid' field instead"


def _normalize_id_predicate(predicate, component_type):
    if predicate.field.name == 'id' and isinstance(predicate.value, str):
        warn_deprecation(_UID_DEPRECATION_MSG)
        return FieldFilter(component_type.fields.uid, predicate.operator_name, predicate.value)
    return predicate


class InfiniBoxSystemComponents(SystemComponentsBinder):

    def __init__(self, system):
        super(InfiniBoxSystemComponents, self).__init__(InfiniBoxSystemComponent, system)
        self.system_component = System(self.system, {'parent_id': "", 'id': 0})
        self.cache_component(self.system_component)
        RackType = self.racks.object_type
        self._rack_1 = RackType(self.system, {'parent_id': self.system_component.id, 'rack': 1})
        self.cache_component(self._rack_1)
        self._initialize()

    def _initialize(self):
        self._fetched_nodes = False
        self._fetched_others = False
        self._fetched_service_clusters = False
        self._fetched_external_clusters = False
        self._deps_by_compoents_tree = defaultdict(set)
        self._initialization_uuid = uuid.uuid4()

    def invalidate_cache(self):
        super(InfiniBoxSystemComponents, self).invalidate_cache()
        self._initialize()

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

    def should_fetch_external_clusters(self):
        return not self._fetched_external_clusters

    def mark_fetched_nodes(self):
        self._fetched_nodes = True

    def mark_fetched_all(self):
        self._fetched_others = True
        self._fetched_nodes = True

    def mark_fetched_service_clusters(self):
        self._fetched_service_clusters = True

    def mark_fetched_external_clusters(self):
        self._fetched_external_clusters = True

    def get_rack_1(self):
        return self._rack_1

    def find(self, *predicates, **kw):
        component_name = kw.pop('component_type', None)
        if component_name is None:
            return InfiniBoxGenericComponentQuery(self.system, *predicates, **kw)
        component_type = self._COMPONENTS_BY_TYPE_NAME[component_name]  # pylint: disable=unsubscriptable-object
        component_collection = self.system.components[component_type]
        return component_collection.find(*predicates, **kw)

    @contextmanager
    def fetch_tree_once_context(self, force_fetch=True, with_logging=True):
        component_roots = [self.racks, self.service_clusters, self.systems]
        with ExitStack() as ctx:
            for component_binder in component_roots:
                ctx.enter_context(component_binder.fetch_tree_once_context(force_fetch=force_fetch,
                                                                           with_logging=with_logging))
            yield


class ComputedIDBinding(InfiniSDKBinding):

    def get_api_value_from_value(self, system, objtype, obj, value):
        return int(value.rsplit(':', 1)[1])

    def get_value_from_api_object(self, system, objtype, obj, api_obj):
        parent_id = api_obj.get('parent_id', '')
        returned = "{}_".format(parent_id) if parent_id else ""
        index = objtype.fields.index.binding.get_value_from_api_object(system, objtype, obj, api_obj)
        returned += '{}:{}'.format(objtype.get_type_name(), index)
        return returned

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        raise NotImplementedError() # pragma: no cover


class InfiniBoxComponentBinder(MonomorphicBinder):

    _force_fetching_from_cache = False

    def should_force_fetching_from_cache(self):
        return self._force_fetching_from_cache

    def get_by_uid(self, uid):
        return self.get(uid=uid)

    def get_by_id_lazy(self, id):  # pylint: disable=redefined-builtin
        returned = self.safe_get_by_id(id)
        if returned is None:
            raise NotImplementedError(
                "Initializing infinibox components lazily is not yet supported") # pragma: no cover
        return returned

    def find(self, *predicates, **kw):
        if isinstance(kw.get('id', None), str):
            warn_deprecation(_UID_DEPRECATION_MSG)
            kw['uid'] = kw.pop('id')
        return InfiniBoxComponentQuery(self.system, self.object_type,
                                       *(_normalize_id_predicate(pred, self.object_type) for pred in predicates),
                                       **kw)

    @deprecated(message="Use to_list/count instead", since='63.0')
    def __len__(self):
        return len(self.find())

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
        # Don't add the second context to the ExitStack. For more information see INFRADEV-5884
        with ExitStack() as stack, self.force_fetching_from_cache_context():
            for obj_type in self.system.components.get_depended_components_type(self.object_type):
                obj_collection = self.system.components[obj_type]
                stack.enter_context(obj_collection.force_fetching_from_cache_context())
            yield

    @contextmanager
    def fetch_tree_once_context(self, force_fetch=True, with_logging=True):
        is_forced_cache = self.should_force_fetching_from_cache()
        if not is_forced_cache:
            if with_logging:
                _logger.debug('Entering fetch tree once of {}', self)
            self._fetch_tree(force_fetch)
        with self._force_fetching_tree_from_cache_context():
            yield
        if not is_forced_cache and with_logging:
            _logger.debug('Exiting fetch tree once of {}', self)


    def _fetch_tree(self, force_fetch):
        components = self.system.components
        if self.object_type in [components.nodes.object_type,
                                components.services.object_type,
                                components.ib_ports.object_type,
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
        elif self.object_type is components.external_clusters.object_type:
            if force_fetch or components.should_fetch_external_clusters():
                self._fetch_external_clusters()
        else:
            if force_fetch or components.should_fetch_all():
                rack_1 = components.get_rack_1()
                rack_1.refresh_cache()

    def _fetch_service_clusters(self):
        components = self.system.components
        service_cluster_type = components.service_clusters.object_type
        url = service_cluster_type.get_url_path(self.system)
        clusters_data = self.system.api.get(url).get_result()
        components.mark_fetched_service_clusters()
        for cluster_data in clusters_data:
            service_cluster_type.construct(self.system, cluster_data, None)

    def _fetch_external_clusters(self):
        components = self.system.components
        service_cluster_type = components.external_clusters.object_type
        url = service_cluster_type.get_url_path(self.system)
        clusters_data = self.system.api.get(url).get_result()
        components.mark_fetched_external_clusters()
        for cluster_data in clusters_data:
            service_cluster_type.construct(self.system, cluster_data, None)


class InfiniBoxSystemComponent(BaseSystemObject):
    BINDER_CLASS = InfiniBoxComponentBinder
    BASE_URL = URL("components")
    UID_FIELD = "uid"
    FIELDS = [
        Field("uid", binding=ComputedIDBinding(), is_identity=True, cached=True),
        Field("parent_id", cached=True, add_updater=False, is_identity=True),
    ]

    @deprecated(message="Use get_uid() instead", since='112.0.0')
    def get_id(self):
        return self.get_uid()

    def is_in_system(self):
        return self._construct_uuid == self.system.components._initialization_uuid  # pylint: disable=protected-access

    def __deepcopy__(self, memo):
        return self.construct(self.system, copy.deepcopy(self._cache, memo), self.get_parent_id())

    def invalidate_cache(self, *field_names):
        non_invalidated_fields = set(name for field in self.fields for name in (field.name, field.api_name)
                                     if field.is_identity)
        field_names_to_invalidate = set(field_names or self._cache.keys()) - set(non_invalidated_fields)
        if field_names_to_invalidate:
            super(InfiniBoxSystemComponent, self).invalidate_cache(*field_names_to_invalidate)
        else:
            assert not field_names, \
                "Cannot invalidate only these fields: {}".format(', '.join(non_invalidated_fields))

    def _deduce_from_cache(self, field_names, from_cache):
        collection = self.system.components[self.get_plural_name()]
        if collection.should_force_fetching_from_cache():
            return True
        return super(InfiniBoxSystemComponent, self)._deduce_from_cache(field_names, from_cache)

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

    def get_binder(self):
        return self.system.components[self.get_plural_name()]
    get_collection = get_binder

    @classmethod
    def _iter_sub_component_fields(cls, system):
        for field in cls.fields:
            if system.is_field_supported(field) and isinstance(field.binding, ListOfRelatedComponentBinding):
                yield field


    def get_sub_components(self):
        for field in self._iter_sub_component_fields(self.system):
            for component in self.get_field(field.name):
                yield component

    def refresh_cache(self):
        data = self.system.api.get(self.get_this_url_path()).get_result()
        self.construct(self.system, data, self.get_parent_id())


    @classmethod
    def construct(cls, system, data, parent_id, allow_partial_fields=False):    # pylint: disable=arguments-differ
        # pylint: disable=protected-access
        data['parent_id'] = parent_id
        component_id = cls.fields[cls.UID_FIELD].binding.get_value_from_api_object(system, cls, None, data)
        returned = system.components.try_get_component_by_id(component_id)
        if returned is None:
            component_type = cls.get_type_name()
            object_type = system.components._COMPONENTS_BY_TYPE_NAME.get(component_type, InfiniBoxSystemComponent)
            returned = object_type(system, data)
            system.components._deps_by_compoents_tree[type(returned.get_parent())].add(object_type)
            system.components.cache_component(returned)
        else:
            returned.update_field_cache(data)
        for field in cls._iter_sub_component_fields(system):
            try:
                field.binding.get_value_from_api_object(system, cls, returned, data)
            except KeyError:
                if not allow_partial_fields:
                    raise
        returned._construct_uuid = system.components._initialization_uuid
        return returned



@InfiniBoxSystemComponents.install_component_type
class Rack(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="rack", type=int, is_identity=True),
        Field("enclosures", type=list, binding=ListOfRelatedComponentBinding()),
        Field("nodes", type=list, binding=ListOfRelatedComponentBinding()),
        Field("bbus", api_name='ups', type=list, binding=ListOfRelatedComponentBinding()),
        Field("pdus", type=list, binding=ListOfRelatedComponentBinding()),
    ]

    @classmethod
    def get_specific_rack_url(cls, rack_id):
        if rack_id == 1:
            return cls.BASE_URL
        racks_url = cls.BASE_URL.add_path(cls.get_plural_name())
        return racks_url.add_path(str(rack_id))

    @cached_method
    def get_this_url_path(self):
        return self.get_specific_rack_url(self.get_index())

    def refresh_without_enclosures(self):
        fields = ",".join(field.api_name for field in self.fields
                          if field.name not in ('enclosures', 'uid', 'parent_id'))
        url = self.get_this_url_path().add_query_param('fields', fields)
        data = self.system.api.get(url).get_result()
        self.system.components.mark_fetched_nodes()
        data['enclosures'] = []
        self.construct(self.system, data, self.get_parent_id())

    def is_in_system(self):
        return True

    def refresh_cache(self):
        self.system.components.mark_fetched_all()
        super(Rack, self).refresh_cache()


@InfiniBoxSystemComponents.install_component_type
class Enclosure(InfiniBoxSystemComponent):
    FIELDS = [
        Field("api_id", api_name="id", type=int, cached=True),
        Field("index", api_name="id", type=int, is_identity=True),
        Field("drives", type=list, binding=ListOfRelatedComponentBinding()),
        Field("state", cached=False),
    ]


class Nodes(InfiniBoxComponentBinder):

    def get_by_wwpn(self, wwpn):
        fc_port = self.system.components.fc_ports.safe_get(wwpn=wwpn)
        if fc_port is not None:
            return fc_port.get_node()

    def get_by_ip(self, ip_address):
        with self.system.network_interfaces.fetch_once_context():
            for ns in self.system.network_spaces.get_all():
                for ip in ns.get_ips(from_cache=True):
                    if ip.interface_id is None:
                        continue
                    if ip.ip_address == ip_address:
                        return self.system.network_interfaces.get_by_id_lazy(ip.interface_id).get_node()

    def refresh_fields(self, field_names):
        assert isinstance(field_names, (list, tuple)), "field_names must be either a list or a tuple"
        field_names_str = ",".join(set(field_names).union(['id']))
        url = self.object_type.get_url_path(self.system).set_query_param('fields', field_names_str)
        data = self.system.api.get(url).get_result()
        parent_id = self.system.components.get_rack_1().get_uid()
        return [self.object_type.construct(self.system, obj_data, parent_id, True) for obj_data in data]


@InfiniBoxSystemComponents.install_component_type
class Node(InfiniBoxSystemComponent):
    BINDER_CLASS = Nodes
    FIELDS = [
        Field("api_id", api_name="id", type=int, cached=True),
        Field("index", api_name="id", type=int, is_identity=True),
        Field("name", cached=True),
        Field("model", cached=True),
        Field("ib_ports", type=list, binding=ListOfRelatedComponentBinding()),
        Field("fc_ports", type=list, binding=ListOfRelatedComponentBinding()),
        Field("eth_ports", type=list, binding=ListOfRelatedComponentBinding()),
        Field("drives", type=list, binding=ListOfRelatedComponentBinding("local_drives")),
        Field("services", type=list, binding=ListOfRelatedComponentBinding()),
        Field("state", cached=False),
        Field("security", cached=False, type=MunchType, feature_name='fips'),
        Field("tpm", cached=False, type=MunchType, feature_name='fips'),
    ]

    def is_active(self, **kwargs):
        return self.get_state(**kwargs) == 'ACTIVE'

    def is_degraded(self, **kwargs):
        return self.get_state(**kwargs) == 'DEGRADED'

    def is_failed(self, **kwargs):
        return self.get_state(**kwargs) == 'FAILED'

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


@InfiniBoxSystemComponents.install_component_type
class LocalDrive(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="drive_index", type=int, is_identity=True),
        Field("model"),
        Field("vendor"),
        Field("firmware"),
        Field("state", cached=False),
        Field("type"),
        Field("serial_number"),
        Field("node", api_name="node_index", type=int, cached=True, binding=RelatedComponentBinding()),
        Field("encryption_state", type=bool, feature_name="fips"),
    ]

    @classmethod
    def get_type_name(cls):
        return "local_drive"

    @cached_method
    def get_this_url_path(self):
        parent_url = self.get_parent().get_this_url_path()
        this_url = parent_url.add_path("drives").add_path(str(self.get_index()))
        return this_url

    def is_active(self, **kwargs):
        return self.get_state(**kwargs) == 'OK'

    def is_ssd(self, **kwargs):
        return self.get_type(**kwargs) == 'SSD'


@InfiniBoxSystemComponents.install_component_type
class EthPort(InfiniBoxSystemComponent):
    FIELDS = [
        Field("api_id", api_name="id", type=int, cached=True),
        Field("hw_addr", is_identity=True),
        Field("connection_speed", type=int),
        Field("max_speed", type=int, feature_name="max_speed"),
        Field("device_name", api_name="name"),
        Field("port_number", type=int, cached=True),
        Field("index", api_name="id", type=int, is_identity=True),
        Field("node", api_name="node_index", type=int, cached=True, binding=RelatedComponentBinding()),
        Field("role", cached=True),
        Field("name", cached=True),
        Field("system_interface_port_number", type=int),
        Field("state", cached=False),
        Field("link_state", cached=False),
        Field("ip_v4_addr"),
        Field("ip_v4_broadcast"),
        Field("ip_v4_netmask"),
        Field("ip_v6_addr"),
        Field("ip_v6_netmask"),
    ]

    @classmethod
    def get_type_name(cls):
        return "eth_port"

    def is_link_up(self, **kwargs):
        if self.get_state(**kwargs) != 'OK':
            return False
        return self.get_link_state(**kwargs).lower() in ("link up", "up")


@InfiniBoxSystemComponents.install_component_type
class IbPort(InfiniBoxSystemComponent):
    FIELDS = [
        Field("api_id", api_name="id", type=int, cached=True),
        Field("index", api_name="id", type=int, is_identity=True),
        Field("firmware"),
        Field("last_probe_timestamp", type=int),
        Field("link_state", cached=False, new_to="3.0"),
        Field("model", cached=True),
        Field("node", api_name="node_index", type=int, cached=True, binding=RelatedComponentBinding()),
        Field("node_index", type=int, cached=True),
        Field("probe_ttl", type=int),
        Field("state", cached=False),
        Field("state_description", cached=False),
        Field("vendor", cached=True),
    ]

    @classmethod
    def get_type_name(cls):
        return "ib_port"

    def is_link_up(self, *, from_cache=False):
        if not from_cache:
            self.refresh_cache()
        if self.get_state(from_cache=True) != 'OK':
            return False
        if not self.is_field_supported('link_state'):
            return True
        link_state = self.get_link_state(from_cache=True)
        return link_state and link_state.lower() == "up"


class FcPorts(InfiniBoxComponentBinder):
    def get_online_target_addresses(self, from_cache=False):
        addresses = []
        ctx = self.force_fetching_from_cache_context if from_cache else self.fetch_tree_once_context
        with ctx():
            for fc_port in self:
                if fc_port.is_link_up():
                    addresses.extend(fc_port.get_target_addresses())
        return addresses


@InfiniBoxSystemComponents.install_component_type
class FcPort(InfiniBoxSystemComponent):
    BINDER_CLASS = FcPorts
    FIELDS = [
        Field("api_id", api_name="id", type=int, cached=True),
        Field("index", api_name="id", type=int, is_identity=True),
        Field("wwpn", is_identity=True, cached=True, type=WWNType),
        Field("node", api_name="node_index", type=int, cached=True, binding=RelatedComponentBinding()),
        Field("state", cached=False),
        Field("link_state", cached=False),
        Field("role", cached=True),
        Field("soft_target_addresses", type=list, cached=True),
        Field("switch_vendor", cached=True),
        Field("enabled", type=bool),
    ]

    def is_link_up(self, **kwargs):
        if not self.is_enabled(**kwargs):
            return False
        if self.get_state(**kwargs) != 'OK':
            return False
        return self.get_link_state(**kwargs).lower() in ("link up", "up")

    @classmethod
    def get_type_name(cls):
        return "fc_port"

    def is_hard_port(self, **kwargs):
        if self.system.compat.has_npiv():
            return self.get_role(**kwargs) == 'HARD_PORT'
        return True

    def is_soft_port(self, **kwargs):
        if self.system.compat.has_npiv():
            return self.get_role(**kwargs) == 'SOFT_PORT'
        return False

    def get_target_addresses(self, **kwargs):
        if self.is_soft_port(**kwargs):
            return self.get_soft_target_addresses(**kwargs)
        return set([self.get_wwpn(**kwargs)])

    def enable(self, role):
        """Enables the FC port with the specified role (SOFT_PORT/HARD_PORT)"""
        self.system.api.post(self.get_this_url_path().add_path('enable'), data={'role': role})
        self.invalidate_cache('enabled')

    def disable(self):
        """Disables the FC Port"""
        self.system.api.post(self.get_this_url_path().add_path('disable'), data={})
        self.invalidate_cache('enabled')


@InfiniBoxSystemComponents.install_component_type
class Drive(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="drive_index", type=int, is_identity=True),
        Field("enclosure_index", type=int, cached=True),
        Field("enclosure", api_name="enclosure_index", type=int, cached=True, binding=RelatedComponentBinding()),
        Field("serial_number"),
        Field("capacity", api_name="bytes_capacity", type=CapacityType),
        Field("state", cached=False),
        Field("encryption_state", type=bool, feature_name="fips"),
    ]

    def get_paths(self, from_cache=False):
        node_access_flags = self.get_field('nodes_access', from_cache=from_cache)
        return [node
                for node, can_access_node in zip(self.system.components.nodes, node_access_flags)
                if can_access_node]

    def is_active(self, **kwargs):
        return self.get_state(**kwargs) == 'ACTIVE'


@InfiniBoxSystemComponents.install_component_type
class Service(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="name", is_identity=True),
        Field("name", is_identity=True, cached=True),
        Field("role", cached=False),
        Field("state", cached=False),
    ]

    def get_service_cluster(self):
        try:
            return self.system.components.service_clusters.get(name=self.get_name())
        except ObjectNotFound:
            raise NotImplementedError("This service ({}) doesn't support CLM".format(self.get_name()))

    def is_active(self, **kwargs):
        return self.get_state(**kwargs) == 'ACTIVE'

    def is_inactive(self, **kwargs):
        # Workaround for INFINIBOX-18309 & INFINIBOX-18308 & INFINIBOX-18647 & INFINIBOX-17256
        return self.get_state(**kwargs) in ('INACTIVE', 'PROCESS_FINISHED', 'SHUTDOWN', 'INVALID')

    def is_master(self, **kwargs):
        return self.get_role(**kwargs) == 'MASTER'

    def is_secondary(self, **kwargs):
        return self.get_role(**kwargs) == 'SECONDARY'

    def is_member(self, **kwargs):
        return self.get_role(**kwargs) == 'MEMBER'

    def get_node(self):
        return self.get_parent()


@InfiniBoxSystemComponents.install_component_type
class ServiceCluster(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="name", is_identity=True),
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

    def is_active(self, **kwargs):
        return self.get_state(**kwargs) == 'ACTIVE'

    def is_inactive(self, **kwargs):
        return self.get_state(**kwargs) in ('INACTIVE', 'SHUTDOWN')

    def is_degraded(self, **kwargs):
        return self.get_state(**kwargs) == 'DEGRADED'


def _ensure_elastic(func):
    def inner(self, *args, **kwargs):
        if not self.get_name() == 'elastic':
            raise NotImplementedError("The getter for cluster {} is not support".format(self.get_name()))
        return func(self, *args, **kwargs)
    return inner

@InfiniBoxSystemComponents.install_component_type
class ExternalServiceCluster(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="name", is_identity=True),
        Field("name", is_identity=True, cached=True),
        Field("state", api_name="cluster_state", cached=False),
        Field("node_states", type=list),
        ]

    @classmethod
    def get_type_name(cls):
        return "external_cluster"

    @classmethod
    def get_url_path(cls, system):
        return URL('external_services')

    @cached_method
    def get_this_url_path(self):
        services_url = self.get_url_path(self.system)
        this_url = services_url.add_path(str(self.get_index()))
        return this_url

    @classmethod
    def is_supported(cls, system): # pylint: disable=unused-argument
        return system.compat.has_events_db()

    @_ensure_elastic
    def is_steady(self, **kwargs):
        return self.get_field("health", **kwargs)["initializing_shards"] == 0

    @_ensure_elastic
    def is_active(self, **kwargs):
        return self.get_state(**kwargs) == 'GREEN'

    @_ensure_elastic
    def is_degraded(self, **kwargs):
        return self.get_state(**kwargs) == 'YELLOW'


@InfiniBoxSystemComponents.install_component_type
class BBU(InfiniBoxSystemComponent):
    FIELDS = [
        Field("api_id", api_name="id", type=int, cached=True),
        Field("index", api_name="id", type=int, is_identity=True),
        Field("state", cached=False),
        Field("on_battery", api_name="onBattery", type=bool, cached=False),
        Field("charging", type=bool, cached=False),
    ]

    @classmethod
    def get_url_path(cls, system):
        return cls.BASE_URL.add_path('ups')

    @cached_method
    def get_this_url_path(self):
        return self.get_url_path(self.system).add_path(str(self.get_index()))


@InfiniBoxSystemComponents.install_component_type
class PDU(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, is_identity=True),
        Field("api_id", api_name="id", type=int, is_identity=True),
        Field("model"),
        Field("vendor"),
        Field("firmware"),
        Field("state", cached=False),
        Field("state_description"),
        Field("power_ports", type=MunchListType),
        Field("power_consumption", type=int),
        Field("probe_ttl", type=int),
        Field("last_probe_timestamp", type=int),
    ]

    @classmethod
    def get_url_path(cls, system):
        return cls.BASE_URL.add_path(cls.get_plural_name())

    @cached_method
    def get_this_url_path(self):
        return self.get_url_path(self.system).add_path(str(self.get_index()))


@InfiniBoxSystemComponents.install_component_type
class System(InfiniBoxSystemComponent):
    FIELDS = [
        Field("api_id", api_name="id", type=int, cached=True, is_identity=True),
        Field("index", api_name="id", type=int, is_identity=True),
        Field("operational_state", type=dict, cached=False),
        Field("security", type=dict, feature_name='fips'),
    ]

    @cached_method
    def get_this_url_path(self):
        return URL('system')

    def is_in_system(self):
        return True

    def get_state(self, *args, **kwargs):
        return self.get_operational_state(*args, **kwargs)['state']

    def safe_get_state(self, **kwargs):
        try:
            return self.get_state(**kwargs)
        except Exception:  # pylint: disable=broad-except
            return None

    def is_active(self, **kwargs):
        return self.safe_get_state(**kwargs) == 'ACTIVE'

    def is_stand_by(self, **kwargs):
        return self.safe_get_state(**kwargs) == 'STANDBY'

    def is_down(self, **kwargs):
        return self.safe_get_state(**kwargs) is None

    def refresh_cache(self):
        data = self.system.api.get(self.get_this_url_path()).get_result()
        self.update_field_cache(data)
