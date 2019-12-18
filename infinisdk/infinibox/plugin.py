from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from ..core.translators_and_types import MunchType


class Plugin(SystemObject):
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("type", type=str, is_filterable=True, creation_parameter=True, cached=True),
        Field("name", type=str, is_filterable=True, mutable=True, creation_parameter=True, is_sortable=True,
              default=Autogenerate("plugin_{uuid}")),
        Field("version", type=str, is_filterable=True, creation_parameter=True, mutable=True),
        Field("api_redirect_suffix", type=str, is_sortable=True, creation_parameter=True,
              mutable=True, is_filterable=True),
        Field("management_url", type=str, creation_parameter=True, mutable=True),
        Field("max_sec_without_heartbeat", type=int, creation_parameter=True, mutable=True),
        Field("last_heartbeat", type=int, mutable=True, is_sortable=True, is_filterable=True),
        Field("heartbeat_valid", type=bool, is_filterable=True),
        Field("heartbeat", type=MunchType, mutable=True, add_updater=False),
        Field("tenant", api_name="tenant_id", binding=RelatedObjectBinding('tenants'), cached=True,
              type='infinisdk.infinibox.tenant:Tenant', feature_name='tenants', is_filterable=True, is_sortable=True),
    ]

    def send_heartbeat(self, data):
        return self.system.api.put(self.get_this_url_path().add_path('heartbeat'), data=data)

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_tenants()
