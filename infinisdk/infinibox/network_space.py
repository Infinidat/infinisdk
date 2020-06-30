import http.client as httplib

from mitba import cached_method
from sentinels import NOTHING

from ..core import Field
from ..core.translators_and_types import MunchType, MunchListType
from ..core.bindings import ListOfRelatedObjectIDsBinding, RelatedObjectBinding
from ..core.api.special_values import Autogenerate
from ..core.exceptions import APICommandFailed, CacheMiss
from .system_object import InfiniBoxObject


class NetworkSpace(InfiniBoxObject):
    URL_PATH = 'network/spaces'

    FIELDS = [
        Field("id", is_identity=True, type=int, is_filterable=True, is_sortable=True, cached=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("network_space_{uuid}")),
        Field("network_config", creation_parameter=True, mutable=True, type=MunchType),
        Field("interfaces", creation_parameter=True, mutable=True, type=list,
              binding=ListOfRelatedObjectIDsBinding('network_interfaces')),
        Field("service", creation_parameter=True, default="NAS_SERVICE"),
        Field("ips", creation_parameter=False, mutable=False, type=MunchListType),
        Field("properties", creation_parameter=True, mutable=True, optional=True, type=MunchType),
        Field("automatic_ip_failback", creation_parameter=True, mutable=True, optional=True, type=bool),
        Field("mtu", type=int, creation_parameter=True, mutable=True, optional=True),
        Field("rate_limit", type=int, creation_parameter=True, mutable=True, optional=True),
        Field("tenant", api_name="tenant_id", binding=RelatedObjectBinding('tenants'),
              type='infinisdk.infinibox.tenant:Tenant', feature_name='tenants',
              is_filterable=True, is_sortable=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_network_configuration()

    @classmethod
    def get_type_name(cls):
        return 'network_space'

    def add_ip_address(self, ip_address):
        res = self.system.api.post(self.get_this_url_path().add_path("ips"), data=ip_address).get_result()
        self.invalidate_cache('ips')
        return res

    def _get_specific_ip_url(self, ip_address):
        return self.get_this_url_path().add_path('ips').add_path(ip_address)

    def remove_ip_address(self, ip_address):
        url = self._get_specific_ip_url(ip_address)
        res = self.system.api.delete(url).get_result()
        self.invalidate_cache('ips')
        return res

    def disable_ip_address(self, ip_address):
        returned = self.system.api.post(self._get_specific_ip_url(ip_address).add_path('disable'))
        self.invalidate_cache('ips')
        return returned

    def enable_ip_address(self, ip_address):
        returned = self.system.api.post(self._get_specific_ip_url(ip_address).add_path('enable'))
        self.invalidate_cache('ips')
        return returned

    def get_links(self):
        return self.system.links.find(local_replication_network_space_id=self.id)

    def get_mgmt_ip(self):
        if self.get_service().lower() != "rmr_service":
            raise NotImplementedError('get_mgmt_ip() is supported only on RMR network spaces')
        for ip in self.get_ips():
            if ip.get('type') == "MANAGEMENT":
                return ip
        return self.get_ips()[0]

    @property
    @cached_method
    def routes(self):
        return Routes(self)


class Route:
    def __init__(self, network_space, initial_data):
        self.network_space = network_space
        self.id = initial_data['id']
        self.system = network_space.system
        self._cache = initial_data

    def __repr__(self):
        return '<{}:Route id={}, Network space={!r}>'.format(self.system.get_name(), self.id, self.network_space)

    @cached_method
    def get_this_url_path(self):
        return self.network_space.routes.get_url_path().add_path(str(self.id))

    def delete(self):
        self.system.api.delete(self.get_this_url_path())

    def safe_delete(self):
        try:
            self.delete()
        except APICommandFailed as e:
            if e.status_code != httplib.NOT_FOUND:
                raise

    def update_field(self, field_name, field_value):
        self.system.api.put(self.get_this_url_path(), data={field_name: field_value})

    def get_field(self, field_name, from_cache=False):
        if not from_cache:
            field_data = \
                self.system.api.get(self.get_this_url_path().add_query_param('fields', field_name)).get_result()
            self._cache.update(field_data)

        value = self._cache.get(field_name, NOTHING)
        if value is NOTHING:
            raise CacheMiss("The field {} could not be obtained from cache".format(field_name))

        return value

    def _update_cache(self, new_data):
        self._cache.update(new_data)

    def __eq__(self, other):
        return self.get_unique_key() == other.get_unique_key()

    def get_unique_key(self):
        return (self.system, type(self).__name__, self.id, self.network_space)

    def is_in_system(self):
        """
        Returns whether or not the object actually exists
        """
        try:
            self.get_field('id', from_cache=False)
        except APICommandFailed as e:
            if e.status_code != httplib.NOT_FOUND:
                raise
            return False
        else:
            return True


class Routes:
    def __init__(self, network_space):
        self._network_space = network_space
        self.system = self._network_space.system

    def __repr__(self):
        return '<{}:NetworkSpace id={}.routes>'.format(self.system.get_name(), self._network_space.id)

    @cached_method
    def get_url_path(self):
        return self._network_space.get_this_url_path().add_path('routes')

    def create(self, **data):
        returned = self.system.api.post(self.get_url_path(), data=data).get_result()
        return Route(self._network_space, returned)

    def to_list(self):
        routes_result = self.system.api.get(self.get_url_path()).get_result()
        return [Route(self._network_space, raw_route) for raw_route in routes_result]
