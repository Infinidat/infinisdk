# pylint: disable=no-member
from ..core import Field, MillisecondsDatetimeType
from ..core.bindings import RelatedObjectBinding
from ..core.system_object import SystemObject
from ..core.translators_and_types import MillisecondsDeltaType


class RgReplica(SystemObject):
    URL_PATH = "rg_replicas"
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, cached=True),
        Field("replica_configuration_guid", is_filterable=True, is_sortable=True),
        Field(
            "link",
            api_name="link_id",
            binding=RelatedObjectBinding("links"),
            type="infinisdk.infinibox.link:Link",
            creation_parameter=True,
        ),
        Field("local_link_guid", cached=True),
        Field(
            "pool",
            type="infinisdk.infinibox.pool:Pool",
            api_name="pool_id",
            is_filterable=True,
            is_sortable=True,
            binding=RelatedObjectBinding(),
        ),
        Field(
            "remote_pool_id",
            type=int,
            api_name="remote_pool_id",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "replication_group",
            api_name="replication_group_id",
            binding=RelatedObjectBinding("replication_groups"),
            type="infinisdk.infinibox.replication_group:ReplicationGroup",
            creation_parameter=True,
        ),
        Field(
            "remote_replication_group_id",
            type=int,
            is_filterable=True,
            is_sortable=True,
        ),
        Field("remote_replication_group_name", is_filterable=True, is_sortable=True, cached=True),
        Field(
            "remote_replica_id",
            type=int,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "rpo",
            api_name="rpo_value",
            type=MillisecondsDeltaType,
            mutable=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            optional=True,
        ),
        Field(
            "sync_interval",
            type=MillisecondsDeltaType,
            mutable=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            optional=True,
        ),
        Field("role", cached=False, is_filterable=True),
        Field("replication_type", is_filterable=True, is_sortable=True),
        Field("base_action", creation_parameter=True, optional=True, cached=True),
        Field(
            "created_at",
            type=MillisecondsDatetimeType,
            is_filterable=True,
            is_sortable=True,
            cached=True,
        ),
        Field(
            "updated_at",
            type=MillisecondsDatetimeType,
            is_filterable=True,
            is_sortable=True,
        ),
        Field('state', type=str, cached=False, is_filterable=True),
        Field('state_description', cached=False),
        Field('state_reason', cached=False),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_vvol_replication()

    @classmethod
    def get_type_name(cls):
        return "rg_replica"

    def sync(self):
        """
        Starts a sync job
        """
        returned = self.system.api.post(self.get_this_url_path().add_path('sync'),
                                        headers={'X-INFINIDAT-RAW-RESPONSE': 'true'})
        result = returned.get_result()
        return result
