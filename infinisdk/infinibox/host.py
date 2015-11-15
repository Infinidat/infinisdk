from .._compat import requests

from ..core import Field, MillisecondsDatetimeType
from ..core.type_binder import TypeBinder
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import APICommandFailed
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxLURelatedObject
from infi.dtypes.wwn import WWN


class HostBinder(TypeBinder):
    """Implements *system.hosts*
    """

    def get_host_id_by_initiator_address(self, address):
        """:returns: an id of a host object defined on a system having the specified FC address configured, None if none exists
        """
        try:
            res = self.system.api.get("hosts/host_id_by_initiator_address/{0}".format(address), check_version=False)
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
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("host_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("ports", type=list, add_getter=False, add_updater=False),
        Field("cluster", api_name="host_cluster_id", type='infinisdk.infinibox.host_cluster:HostCluster', is_filterable=True, binding=RelatedObjectBinding('host_clusters')),
        Field("host_type", creation_parameter=True, optional=True, mutable=True),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
    ]

    def _add_port(self, port_type, port_address):
        port_wwn = str(WWN(port_address))
        data = dict(address=port_wwn, type=port_type)
        url = "{0}/ports".format(self.get_this_url_path())
        self.system.api.post(url, data=data)
        self.refresh('ports')

    def _remove_port(self, port_type, port_address):
        port_wwn = str(WWN(port_address))
        url = "{0}/ports/{1}/{2}".format(self.get_this_url_path(),
                                         port_type, port_wwn)
        self.system.api.delete(url)
        self.refresh('ports')

    def add_fc_port(self, port_address):
        """
        Adds an FC port address (WWN) to this host
        :param port_address: A string representing the WWN to add (e.g. ``00:11:22:33:44:55:66``)
        """
        return self._add_port('fc', port_address)

    def remove_fc_port(self, port_address):
        """
        Removes a FC port address (WWN) to this host
        """
        return self._remove_port('fc', port_address)

    def get_fc_ports(self):
        """
        Returns all FC ports defined on this host
        """
        return self._get_ports('fc')

    def _get_ports(self, port_type):
        lowered_port_type = port_type.lower()
        return [WWN(port['address'])
                for port in self.get_field('ports')
                    if port['type'].lower() == lowered_port_type]
