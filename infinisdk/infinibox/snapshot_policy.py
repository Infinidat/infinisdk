import mitba
from munch import munchify

from infinisdk.core.system_object import SystemObject

from ..core import Field
from ..core.api.special_values import Autogenerate
from ..core.type_binder import SubObjectTypeBinder
from .cons_group import ConsGroup
from .filesystem import Filesystem
from .schedule import Schedule
from .volume import Volume


class SnapshotPolicy(SystemObject):
    URL_PATH = "snapshot_policies"

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field(
            "name",
            creation_parameter=True,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            default=Autogenerate("snapshot_{uuid}"),
        ),
        Field(
            "suffix",
            creation_parameter=True,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            default=Autogenerate("-target-{uuid}"),
        ),
        Field(
            "default_snapshot_policy",
            type=bool,
            mutable=True,
            feature_name="snapshot_policies_enhancements",
        ),
        Field(
            "assigned_entities_count",
            type=int,
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "snapshot_policy"

    @classmethod
    def get_plural_name(cls):
        return "snapshot_policies"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_snapshot_policies()

    @mitba.cached_property
    def schedules(self):
        return SubObjectTypeBinder(self.system, Schedule, self)

    def assign_entity(self, entity):
        """
        Assigns an entity that we want to create
        a snapshot for, to the policy.
        """
        entity_to_name_map = {
            ConsGroup: "CG",
            Filesystem: "FILESYSTEM",
            Volume: "VOLUME",
        }
        if entity is not None:
            url = self.get_this_url_path().add_path("assign_entity")
            entity_type = type(entity)
            data = {
                "assigned_entity_id": entity.id,
                "assigned_entity_type": entity_to_name_map[entity_type],
            }
            self.system.api.post(url, data=data)

    def unassign_entity(self, entity):
        """
        Unassigns an entity from the current policy
        """
        url = self.get_this_url_path().add_path("unassign_entity")
        data = {"assigned_entity_id": entity.id}
        self.system.api.post(url, data=data)

    def get_assigned_entities(self, page_size=None, page=None):
        """
        Returns all assigned entities for the
        current policy
        """
        url = self.get_this_url_path().add_path("assigned_entities")
        if page_size is not None:
            assert page_size > 0, "Page size must be a positive integer value"
            url = url.add_query_param("page_size", page_size)
        if page is not None:
            assert page > 0, "Page must be a positive integer value"
            url = url.add_query_param("page", page)
        return munchify(self.system.api.get(url).get_result())
