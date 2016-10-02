from ..core import Field, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxLURelatedObject
from ..core.bindings import ListOfRelatedObjectBinding


class HostCluster(InfiniBoxLURelatedObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("cluster_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("san_client_type", new_to="3.0"),
        Field("hosts", type=list, add_updater=False, binding=ListOfRelatedObjectBinding()),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
    ]

    def add_host(self, host):
        url = "{0}/hosts".format(self.get_this_url_path())
        self.system.api.post(url, data={"id" : host.id})
        self.invalidate_cache('hosts')
        host.invalidate_cache('host_cluster_id')

    def remove_host(self, host):
        url = "{0}/hosts/{1}".format(self.get_this_url_path(), host.id)
        self.system.api.delete(url)
        self.invalidate_cache('hosts')
        host.invalidate_cache('host_cluster_id')

    @classmethod
    def get_type_name(cls):
        return 'host_cluster'

    @classmethod
    def get_url_path(cls, system):
        return '/api/rest/clusters'
