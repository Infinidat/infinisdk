import functools

import gossip

from ..core import Field, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from ..core.utils import end_reraise_context
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

    def remove_member(self, member):
        path = self._get_members_url().add_path(str(member.id))

        trigger_hook = functools.partial(
            gossip.trigger_with_tags,
            kwargs={"replication_group": self, "member": member},
            tags=["infinibox"],
        )
        trigger_hook("infinidat.sdk.pre_replication_group_remove_member")
        try:
            self.system.api.delete(path)
        except Exception:  # pylint: disable=broad-except
            with end_reraise_context():
                trigger_hook("infinidat.sdk.replication_group_remove_member_failure")
        trigger_hook("infinidat.sdk.post_replication_group_remove_member")

    def _get_members_url(self):
        return self.get_this_url_path().add_path("members")
