import itertools
import os
import weakref

import gossip
from mitba import cached_method
from sentinels import NOTHING
from urlobject import URLObject as URL

from ..core.api import APITarget, OMIT
from ..core.config import config, get_ini_option
from ..core.exceptions import CacheMiss, VersionNotSupported
from ..core.object_query import LazyQuery
from ..core.utils.environment import get_hostname, get_logged_in_username, get_infinisdk_version
from .capacities import InfiniBoxSystemCapacity
from .compatibility import Compatibility
from .components import InfiniBoxSystemComponents
from .cons_group import ConsGroup
from .dataset import Datasets
from .fc_switch import FcSwitch
from .fc_soft_target import FcSoftTarget
from .san_client import SanClients
from .events import Events
from .export import Export
from .filesystem import Filesystem
from .qos_policy import QosPolicy
from .nlm_lock import NlmLock
from .host import Host
from .host_cluster import HostCluster
from .initiator import Initiator
from .ldap_config import LDAPConfig
from .link import Link
from .network_interface import NetworkInterface
from .network_space import NetworkSpace
from .notification_rule import NotificationRule
from .notification_target import NotificationTarget
from .pool import Pool
from .plugin import Plugin
from .tenant import Tenant
from .replica import Replica
from .search_utils import get_search_query_object, safe_get_object_by_id_and_type_lazy
from .user import User
from .volume import Volume
from .metadata import SystemMetadata
from .kms import Kms

try:
    from infinisim.core.context import lookup_simulator_by_address
except ImportError:
    lookup_simulator_by_address = None


_DNS_SERVERS_CONFIG_PATH = 'config/mgmt/environment.dns_servers'


class InfiniBox(APITarget):
    OBJECT_TYPES = [Volume, Pool, Host, HostCluster, User, Filesystem, Export,
                    NetworkSpace, NetworkInterface, Link, Replica, LDAPConfig,
                    NotificationTarget, NotificationRule, ConsGroup, Initiator,
                    FcSwitch, FcSoftTarget, QosPolicy, NlmLock, Plugin, Tenant]

    SYSTEM_EVENTS_TYPE = Events
    SYSTEM_COMPONENTS_TYPE = InfiniBoxSystemComponents

    def _initialize(self):
        super(InfiniBox, self)._initialize()
        self.current_user = _CurrentUserProxy(self)
        self.compat = Compatibility(self)
        self.capacities = InfiniBoxSystemCapacity(self)
        self.system_metadata = SystemMetadata(self)
        self._related_systems = []
        self.datasets = Datasets(self)
        self.san_clients = SanClients(self)
        self.kms = Kms(self)

    def check_version(self):
        if not self.compat.can_run_on_system():
            raise VersionNotSupported(self.get_version())

    def is_field_supported(self, field):
        if field.new_to_version and self.compat.get_parsed_system_version() < field.new_to_version:
            return False
        if field.until_version and self.compat.get_parsed_system_version() > field.until_version:
            return False
        return self.compat.is_feature_supported(field.feature_name)

    def _get_api_auth(self):
        username = self._get_auth_ini_option('username', None)
        password = self._get_auth_ini_option('password', None)
        if not username and not password:
            return None
        elif not username:
            username = 'admin'
        elif not password:
            password = ''

        return username, password

    def _get_auth_ini_option(self, key, default):
        for address in itertools.chain([None], self._addresses):
            if address is None:
                section = 'infinibox'
            else:
                section = 'infinibox:{}'.format(address[0])
            returned = get_ini_option(section, key, NOTHING)
            if returned is not NOTHING:
                return returned

        return default

    def _get_api_timeout(self):
        return config.get_path('infinibox.defaults.system_api.timeout_seconds')

    def _is_simulator(self, address):
        return type(address).__name__ == "Infinibox"

    def _get_simulator_address(self, address, use_ssl):
        simulator_address = address.get_floating_addresses()[0]
        return (simulator_address, 443 if use_ssl else 80)

    def get_approval_failure_codes(self):
        d = config.get_path('infinibox.approval_required_codes')
        return d

    def get_luns(self):
        for mapping_obj in itertools.chain(self.host_clusters, self.hosts):
            for lun in mapping_obj.get_luns():
                if lun.is_clustered() and not isinstance(mapping_obj, self.host_clusters.object_type):
                    continue
                yield lun

    luns = property(get_luns)

    def get_state(self):
        return self.components.system_component.get_state()

    def is_simulator(self):
        return self.get_system_info("model").lower() == "infinisim-model"

    def get_simulator(self):
        if lookup_simulator_by_address is None:
            return None
        for url in self.api.urls:
            returned = lookup_simulator_by_address(url.hostname)
            if returned is not None:
                return returned
        return None

    def is_mock(self):
        return "mock" in self.get_system_info("name")

    def get_system_info(self, field_name, **kwargs):
        kwargs.setdefault('fetch_if_not_cached', True)
        kwargs.setdefault('from_cache', True)
        return self.components.system_component.get_field(field_name, **kwargs)

    def get_name(self):
        """
        Returns the name of the system
        """
        try:
            return self.components.system_component.get_field('name', from_cache=True, fetch_if_not_cached=False)
        except CacheMiss:
            return self._get_received_name_or_ip()

    def update_name(self, name):
        """
        Update the name of the system
        """
        self.api.put('/api/rest/system/name/', data=name)
        self.components.system_component.update_field_cache({'name': name})

    def get_serial(self, **kwargs):
        """
        Returns the serial number of the system
        """
        return self.get_system_info('serial_number', **kwargs)

    def get_model_name(self, long_name=False):
        """
        Retrieves the model name as reported by the system
        """
        url = 'config/mgmt/system.model_{}_name'.format('long' if long_name else 'short')
        return self.api.get(url).get_result()

    def get_version(self):
        """
        Returns the product version of the system
        """
        return self.get_system_info('version')

    def get_dns_servers(self):
        ip_addresses = self.api.get(_DNS_SERVERS_CONFIG_PATH).get_result()
        return [ip_address.strip() for ip_address in ip_addresses.split(',')]

    def update_dns_servers(self, *ip_addresses):
        self.api.put(_DNS_SERVERS_CONFIG_PATH, data=','.join(ip_addresses))

    def get_revision(self):
        return self.get_system_info('release')['system']['revision']

    def iter_related_systems(self):
        """
        Iterate the list of systems related to the current system
        """
        dead_system_objects = []
        for ref in self._related_systems:
            system = ref()
            if system:
                yield system
            else:
                dead_system_objects.append(ref)

        for dead in dead_system_objects:
            self._related_systems.remove(dead)

    def register_related_system(self, system):
        """
        Registers another system as related system to the current one
        """
        for registered_system in self.iter_related_systems():
            if system is registered_system:
                return

        self._related_systems.append(weakref.ref(system))

    def unregister_related_system(self, system):
        """
        Unregisters another system from appearing the the current system's related systems
        """
        system_ref = None
        for ref in self._related_systems:
            if ref() == system:
                system_ref = ref

        if system_ref is not None:
            self._related_systems.remove(system_ref)

        self.links.remove_cached_related_system(system)

    def _after_login(self):
        self.components.system_component.refresh_cache()

        gossip.trigger('infinidat.sdk.after_login', system=self)

    def login(self):
        """
        Verifies the current user against the system
        """
        username, password = self.api.get_auth()
        login_data = {"username": username, "password": password}
        if self.compat.has_auth_sessions():
            login_data['clientid'] = self._get_client_id()
        res = self.api.post("users/login", data=login_data)
        self.api.mark_logged_in()
        self._after_login()
        return res

    def is_logged_in(self):
        """Returns True if login() was called on this system, and logout() hasn't been called yet
        """
        return self.api.is_logged_in()

    def mark_logged_in(self):
        self.api.mark_logged_in()

    def mark_not_logged_in(self):
        self.api.mark_not_logged_in()

    def logout(self):
        """
        Logs out the current user
        """
        returned = self.api.post('users/logout', data={})
        self.api.mark_not_logged_in()
        self.api.clear_cookies()
        return returned

    @cached_method
    def _get_client_id(self):
        return 'infinisdk.v{}.{}.{}.{}'.format(
            get_infinisdk_version(),
            get_hostname(),
            get_logged_in_username(),
            os.getpid())

    def _get_v2_metadata_generator(self, **raw_filters):
        for metadata_item in LazyQuery(self, URL('metadata')).extend_url(**raw_filters):
            metadata_item['object'] = safe_get_object_by_id_and_type_lazy(type_name=metadata_item.get('object_type'),
                                                                          object_id=metadata_item['object_id'],
                                                                          system=self)
            yield metadata_item

    def get_all_metadata(self, **raw_filters):
        return self._get_v2_metadata_generator(**raw_filters)

    def is_active(self):
        return self.components.system_component.is_active()

    def is_read_only(self, **kwargs):
        return self.components.system_component.get_operational_state(**kwargs)['read_only_system']

    def search(self, query=OMIT, type_name=OMIT):
        search_query = get_search_query_object(self)
        search_kwargs = {}

        if query is not OMIT:
            search_kwargs['query'] = query

        if type_name is not OMIT:
            search_kwargs['type'] = type_name

        return search_query.extend_url(**search_kwargs)

    def __hash__(self):
        return hash(self.get_name())

    def __eq__(self, other):
        if not isinstance(other, InfiniBox):
            return NotImplemented
        try:
            return self.get_serial(fetch_if_not_cached=False) == other.get_serial(fetch_if_not_cached=False)
        except CacheMiss:
            return self.get_api_addresses() == other.get_api_addresses()

    def __ne__(self, other):
        return not (self == other) # pylint: disable=superfluous-parens


class _CurrentUserProxy:
    def __init__(self, system):
        self.system = system

    def get_owned_pools(self):
        return self.system.pools.get_administered_pools()

    def get_roles(self):
        login_res = self.system.login()
        return login_res.get_result()['roles']
