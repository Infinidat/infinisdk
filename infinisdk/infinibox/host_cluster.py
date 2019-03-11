import gossip
from contextlib import contextmanager
from urlobject import URLObject
from ..core import Field, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxLURelatedObject
from ..core.bindings import ListOfRelatedObjectBinding, RelatedObjectBinding
from ..core.utils import end_reraise_context


class HostCluster(InfiniBoxLURelatedObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("cluster_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("san_client_type", new_to="3.0"),
        Field("hosts", type=list, add_updater=False, binding=ListOfRelatedObjectBinding()),
        Field("host_type", creation_parameter=True, optional=True, mutable=False, is_sortable=True, is_filterable=True,
              feature_name='openvms'),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("tenant", api_name="tenant_id", binding=RelatedObjectBinding('tenants'),
              type='infinisdk.infinibox.tenant:Tenant', feature_name='tenants',
              is_filterable=True, is_sortable=True),
    ]

    @classmethod
    def get_type_name(cls):
        return 'host_cluster'

    @classmethod
    def get_url_path(cls, system):
        return URLObject('/api/rest/clusters')

    @contextmanager
    def _triggering_hooks(self, action_name, kwargs):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.pre_{}'.format(action_name), kwargs, hook_tags)
        try:
            yield
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                kwargs['exception'] = e
                gossip.trigger_with_tags('infinidat.sdk.{}_failure'.format(action_name), kwargs, hook_tags)
        gossip.trigger_with_tags('infinidat.sdk.post_{}'.format(action_name), kwargs, hook_tags)


    def add_host(self, host):
        url = "{}/hosts".format(self.get_this_url_path())
        with self._triggering_hooks('cluster_add_host', {'cluster': self, 'host': host}):
            self.system.api.post(url, data={"id" : host.id})
        self.invalidate_cache('hosts')
        host.invalidate_cache('host_cluster_id')

    def remove_host(self, host):
        url = "{}/hosts/{}".format(self.get_this_url_path(), host.id)
        with self._triggering_hooks('cluster_remove_host', {'cluster': self, 'host': host}):
            self.system.api.delete(url)
        self.invalidate_cache('hosts')
        host.invalidate_cache('host_cluster_id')
