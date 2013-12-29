from ..core import Field
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject


class Cluster(InfiniBoxObject):

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("cluster_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("hosts", api_name="hosts", type=list, add_getter=False, add_updater=False),
    ]

    def add_host(self, host):
        url = "{0}/hosts".format(self.get_this_url_path())
        self.system.api.post(url, data={"id" : host.id})

    def remove_host(self, host):
        url = "{0}/hosts/{1}".format(self.get_this_url_path(), host.id)
        self.system.api.delete(url)

    def get_hosts(self):
        return [self.system.hosts.get_by_id_lazy(host_attrs['id'])
                for host_attrs in self.get_field('hosts')]
