from ..core import Field, MillisecondsDatetimeType
from ..core.bindings import RelatedObjectBinding
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject


class ReplicationGroup(InfiniBoxObject):
    URL_PATH = "replication_groups"

    FIELDS = [
        Field("id", is_identity=True, type=int, cached=True),
        Field(
            "name",
            creation_parameter=True,
            mutable=True,
            default=Autogenerate("replication_group_{uuid}"),
        ),
        Field("uuid"),
        Field(
            "pool",
            type="infinisdk.infinibox.pool:Pool",
            api_name="pool_id",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            binding=RelatedObjectBinding(),
        ),
        Field(
            "replicated",
            api_name="is_replicated",
            type=bool,
            is_filterable=True,
            is_sortable=True,
        ),
        Field("members_count", type=int, is_filterable=True, is_sortable=True),
        Field("created_at", type=MillisecondsDatetimeType),
        Field("updated_at", type=MillisecondsDatetimeType),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_vvol_replication()

    @classmethod
    def get_type_name(cls):
        return "replication_group"
