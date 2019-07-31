from ..core import Field, SystemObject, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.translators_and_types import MunchType


class Tenant(SystemObject):
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("short_tenant_key", type=int, cached=True),
        Field("name", type=str, is_filterable=True, mutable=True, creation_parameter=True,
              default=Autogenerate("tenant_{uuid}")),
        Field("visible_to_sysadmin", type=bool, default=True, creation_parameter=True, optional=True, cached=True),
        Field("capacity", type=MunchType),
        Field("entity_counts", type=MunchType),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("anonymous_gid", type=int, creation_parameter=True, optional=True, mutable=True, is_filterable=True,
              is_sortable=True),
        Field("anonymous_uid", type=int, creation_parameter=True, optional=True, mutable=True, is_filterable=True,
              is_sortable=True),
        Field("nfs_allow_unmapped_users", type=str, mutable=True, is_filterable=True, is_sortable=True,
              creation_parameter=True, optional=True),
        Field("nfs_group_policy", type=str, mutable=True, is_filterable=True, is_sortable=True,
              creation_parameter=True, optional=True)
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_tenants()
