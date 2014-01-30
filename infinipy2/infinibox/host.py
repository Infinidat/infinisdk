from ..core import Field
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxLURelatedObject
from infi.dtypes.wwn import WWN


class Host(InfiniBoxLURelatedObject):

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("host_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("ports", type=list, add_getter=False, add_updater=False),
        Field("host_cluster_id", type=int),
    ]

    def get_cluster(self):
        cluster_id = self.get_host_cluster_id()
        if cluster_id == 0:
            return None
        return self.system.clusters.get_by_id_lazy(cluster_id)

    def _add_port(self, port_type, port_address):
        port_wwn = str(WWN(port_address))
        data = dict(address=port_wwn, type=port_type)
        url = "{0}/ports".format(self.get_this_url_path())
        self.system.api.post(url, data=data)

    def add_fc_port(self, port_address):
        return self._add_port('fc', port_address)

    def add_iscsi_port(self, port_address):
        return self._add_port('iscsi', port_address)

    def remove_fc_port(self, port_address):
        return self._remove_port('fc', port_address)

    def remove_iscsi_port(self, port_address):
        return self._remove_port('iscsi', port_address)

    def _remove_port(self, port_type, port_address):
        url = "{0}/ports/{1}/{2}".format(self.get_this_url_path(),
                                      port_type, port_address)
        self.system.api.delete(url)

    def get_fc_ports(self):
        return self._get_ports('fc')

    def get_iscsi_ports(self):
        return self._get_ports('iscsi')

    def _get_ports(self, port_type):
        lowered_port_type = port_type.lower()
        return [WWN(port['address'])
                for port in self.get_field('ports')
                    if port['type'].lower() == lowered_port_type]
