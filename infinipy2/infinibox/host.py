from ..core import Field
from ..core.bindings import RelatedObjectBinding
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxLURelatedObject
from infi.dtypes.wwn import WWN


class Host(InfiniBoxLURelatedObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("host_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("ports", type=list, add_getter=False, add_updater=False),
        Field("cluster", api_name="host_cluster_id", type='infinipy2.infinibox.cluster:Cluster', is_filterable=True, binding=RelatedObjectBinding()),
    ]

    def purge(self):
        cluster = self.get_cluster(from_cache=False)
        if cluster is not None:
            cluster.remove_host(self)
        for lun in self.get_luns(from_cache=False):
            self.unmap_volume(lun=lun)
        super(Host, self).purge()

    def _add_port(self, port_type, port_address):
        port_wwn = str(WWN(port_address))
        data = dict(address=port_wwn, type=port_type)
        url = "{0}/ports".format(self.get_this_url_path())
        self.system.api.post(url, data=data)
        self.refresh('ports')

    def add_fc_port(self, port_address):
        return self._add_port('fc', port_address)

    def remove_fc_port(self, port_address):
        return self._remove_port('fc', port_address)

    def _remove_port(self, port_type, port_address):
        port_wwn = str(WWN(port_address))
        url = "{0}/ports/{1}/{2}".format(self.get_this_url_path(),
                                         port_type, port_wwn)
        self.system.api.delete(url)
        self.refresh('ports')

    def get_fc_ports(self):
        return self._get_ports('fc')

    def _get_ports(self, port_type):
        lowered_port_type = port_type.lower()
        return [WWN(port['address'])
                for port in self.get_field('ports')
                    if port['type'].lower() == lowered_port_type]
