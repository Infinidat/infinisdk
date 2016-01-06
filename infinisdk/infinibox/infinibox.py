import itertools
import gossip
import weakref

from sentinels import NOTHING
from urlobject import URLObject as URL

from .._compat import iteritems
from ..core.api import APITarget
from ..core.config import config, get_ini_option
from ..core.object_query import LazyQuery
from ..core.exceptions import VersionNotSupported, CacheMiss
from ..core.utils import deprecated
from .host_cluster import HostCluster
from .components import InfiniBoxSystemComponents
from .capacities import InfiniBoxSystemCapacity
from .events import Events
from .host import Host
from .pool import Pool
from .user import User
from .volume import Volume
from .filesystem import Filesystem
from .export import Export
from .network_space import NetworkSpace
from .network_interface import NetworkInterface
from .ldap_config import LDAPConfig
from .notification_target import NotificationTarget
from .notification_rule import NotificationRule
from .link import Link
from .replica import Replica
from .compatability import Compatability
from .cons_group import ConsGroup
from .initiator import Initiator

try:
    from infinisim.core.context import lookup_simulator_by_address
except ImportError:
    lookup_simulator_by_address = None


class InfiniBox(APITarget):
    OBJECT_TYPES = [Volume, Pool, Host, HostCluster, User, Filesystem, Export,
                    NetworkSpace, NetworkInterface, Link, Replica, LDAPConfig,
                    NotificationTarget, NotificationRule, ConsGroup, Initiator]
    SYSTEM_EVENTS_TYPE = Events
    SYSTEM_COMPONENTS_TYPE = InfiniBoxSystemComponents

    def _initialize(self):
        super(InfiniBox, self)._initialize()
        self.current_user = _CurrentUserProxy(self)
        self.compat = Compatability(self)
        self.capacities = InfiniBoxSystemCapacity(self)
        self._related_systems = []

    def check_version(self):
        if not self.compat.can_run_on_system():
            raise VersionNotSupported(self.get_version())

    @property
    @deprecated(message='Use <system>.host_clusters')
    def clusters(self):
        return self.host_clusters

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
                section = 'infinibox:{0}'.format(address[0])
            returned = get_ini_option(section, key, NOTHING)
            if returned is not NOTHING:
                return returned

        return default

    def _get_api_timeout(self):
        return config.get_path('infinibox.defaults.system_api.timeout_seconds')

    def _is_simulator(self, address):
        return type(address).__name__ == "Infinibox"

    def _get_simulator_address(self, address):
        simulator_address = address.get_floating_addresses()[0]
        return (simulator_address, 80)

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
        return "simulator" in self.get_system_info("name")

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

    def get_system_info(self, field_name):
        return self.components.system_component.get_field(field_name,
                                                          from_cache=True,
                                                          fetch_if_not_cached=True)

    def get_name(self):
        """
        Returns the name of the system
        """
        try:
            return self.components.system_component.get_field('name', from_cache=True, fetch_if_not_cached=False)
        except CacheMiss:
            return self._get_received_name_or_ip()

    def get_serial(self):
        """
        Returns the serial number of the system
        """
        return self.get_system_info('serial_number')

    def get_model_name(self):
        """
        Retrieves the model name as reported by the system
        """
        return self.api.get('config/mgmt/system.model_long_name').get_result()

    def get_version(self):
        """
        Returns the product version of the system
        """
        return self.get_system_info('version')

    def get_revision(self):
        if self.compat.get_version_major() < '2':
            return self.get_system_info('revision')
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

    def _after_login(self):
        self.components.system_component.refresh()
        gossip.trigger('infinidat.sdk.after_login', system=self)

    def login(self):
        """
        Verifies the current user against the system
        """
        username, password = self.api.get_auth()
        res = self.api.post("users/login", data={"username": username, "password": password})
        self._after_login()
        return res

    def _get_v1_metadata_generator(self):
        system_metadata = self.api.get('metadata').get_result()
        for object_id, object_dict in iteritems(system_metadata):
            for key, value in iteritems(object_dict):
                yield {'object_id': int(object_id), 'key': key, 'value': value}

    def _get_v2_metadata_generator(self):
        for metadata_item in LazyQuery(self, URL('metadata')):
            metadata_item.pop('id', None)
            yield metadata_item

    def get_all_metadata(self):
        if self.compat.get_metadata_version() < 2:
            return self._get_v1_metadata_generator()
        return self._get_v2_metadata_generator()

    def is_active(self):
        return self.components.system_component.is_active()

    def __hash__(self):
        return self.get_serial()

    def __eq__(self, other):
        if not isinstance(other, InfiniBox):
            return False
        return self.get_serial() == other.get_serial()

    def __ne__(self, other):
        return not (self == other)


class _CurrentUserProxy(object):
    def __init__(self, system):
        self.system = system

    def get_owned_pools(self):
        return self.system.pools.get_administered_pools()

    def get_roles(self):
        login_res = self.system.login()
        return login_res.get_result()['roles']
