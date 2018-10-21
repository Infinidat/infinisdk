from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate
from ..core.translators_and_types import MunchType


class Tenant(SystemObject):
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("short_tenant_key", type=int),
        Field("name", type=str, is_filterable=True, mutable=True, creation_parameter=True,
              default=Autogenerate("tenant_{uuid}")),
        Field("visible_to_sysadmin", type=bool, default=True, creation_parameter=True, optional=True),
        Field("capacity", type=MunchType),
        Field("entity_counts", type=MunchType),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_tenants()
