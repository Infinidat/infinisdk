from __future__ import absolute_import

import requests

from ..core import Field, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import APICommandFailed
from ..core.translators_and_types import host_port_to_api, HostPortListType
from ..core.type_binder import TypeBinder
from .system_object import InfiniBoxLURelatedObject


class HostBinder(TypeBinder):
    """Implements *system.hosts*
    """

    def get_host_id_by_initiator_address(self, address):
        """
        :returns: an id of a host object defined on a system having the specified FC address configured,
          None if none exists
        """
        try:
            res = self.system.api.get("hosts/host_id_by_initiator_address/{}".format(address), check_version=False)
            return res.get_result()
        except APICommandFailed as e:
            if e.response.response.status_code != requests.codes.not_found:
                raise
            return None

    def get_host_by_initiator_address(self, address):
        """:returns: a host object defined on a system having the specified FC address configured, None if none exists
        """
        host_id = self.get_host_id_by_initiator_address(address)
        if host_id is not None:
            return Host(self.system, {'id': host_id})
        return None

    def has_registered_initiator_address(self, address):
        """:returns: whether or not there exists a host object on the system with the specified FC address configured
        """
        return self.get_host_id_by_initiator_address(address) is not None


class Host(InfiniBoxLURelatedObject):

    BINDER_CLASS = HostBinder

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("host_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("san_client_type", new_to="3.0"),
        Field("ports", type=HostPortListType, add_updater=False),
        Field("cluster", api_name="host_cluster_id", type='infinisdk.infinibox.host_cluster:HostCluster',
              is_filterable=True, binding=RelatedObjectBinding('host_clusters')),
        Field("host_type", creation_parameter=True, optional=True, mutable=True, is_sortable=True, is_filterable=True,
              feature_name='openvms'),
        Field("security_method", feature_name='iscsi', creation_parameter=True, optional=True, mutable=True,
              is_sortable=True, is_filterable=True),
        Field("security_chap_inbound_username", creation_parameter=True, feature_name='iscsi', optional=True,
              mutable=True, is_sortable=True, is_filterable=True),
        Field("security_chap_inbound_secret", creation_parameter=True, feature_name='iscsi', hidden=True,
              optional=True, mutable=True),
        Field("security_chap_has_inbound_secret", type=bool, feature_name='iscsi'),
        Field("security_chap_outbound_username", creation_parameter=True, feature_name='iscsi', optional=True,
              mutable=True, is_sortable=True, is_filterable=True),
        Field("security_chap_outbound_secret", creation_parameter=True, feature_name='iscsi', hidden=True,
              optional=True, mutable=True),
        Field("security_chap_has_outbound_secret", type=bool, feature_name='iscsi'),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("optimized", type=bool, mutable=True, is_sortable=True, is_filterable=True,
              creation_parameter=True, optional=True, new_to="5.0"),
        Field("tenant", api_name="tenant_id", binding=RelatedObjectBinding('tenants'),
              type='infinisdk.infinibox.tenant:Tenant', feature_name='tenants',
              is_filterable=True, is_sortable=True),
    ]

    @InfiniBoxLURelatedObject.requires_cache_invalidation("ports")
    def add_port(self, address):
        """
        Adds a port address to this host

        :param address: the port address to add
        :type address: Either an ``infi.dtypes.wwn.WWN`` or ``infi.dtypes.iqn.iSCSIName``. Plain strings are assumed
          to be WWNs
        """
        data = host_port_to_api(address)
        self.system.api.post(self.get_this_url_path().add_path('ports'), data=data)

    @InfiniBoxLURelatedObject.requires_cache_invalidation("ports")
    def remove_port(self, address):
        """
        Removes a port address to this host
        """
        data = host_port_to_api(address)
        url = self.get_this_url_path() \
              .add_path('ports') \
              .add_path(data['type']) \
              .add_path(data['address'])
        self.system.api.delete(url)
