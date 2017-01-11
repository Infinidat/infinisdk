from urlobject import URLObject as URL
from ..core.type_binder import PolymorphicBinder

class SanClients(PolymorphicBinder):

    def __init__(self, system):
        object_types = (system.hosts.object_type, system.host_clusters.object_type)
        super(SanClients, self).__init__(URL('san_clients'), object_types, factory=self._san_client_factory,
                                         system=system)

    def is_supported(self):
        return self.system.compat.get_version_as_float() >= 3.0

    def _san_client_factory(self, system, received_item):
        san_client_type_str = received_item['san_client_type']
        assert san_client_type_str in ('HOST', 'CLUSTER'), 'Unsupported dataset type {}'.format(san_client_type_str)
        san_client_binder = system.hosts if san_client_type_str == 'HOST' else system.host_clusters
        return san_client_binder.object_type.construct(system, received_item)
