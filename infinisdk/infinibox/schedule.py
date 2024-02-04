from ..core import Field
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from ..core.translators_and_types import SecondsDeltaType, TimeOfDayType
from .system_object import InfiniBoxSubObject


class Schedule(InfiniBoxSubObject):
    URL_PATH = "schedules"

    FIELDS = [
        Field(
            "id",
            type=int,
            is_identity=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "snapshot_policy",
            api_name="snapshot_policy_id",
            type="infinisdk.infinibox.snapshot_policy:SnapshotPolicy",
            binding=RelatedObjectBinding("snapshot_policies"),
            is_filterable=True,
            is_sortable=True,
            is_parent_field=True,
        ),
        Field(
            "name",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            default=Autogenerate("schedule_{uuid}"),
        ),
        Field(
            "enabled",
            type=bool,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            add_updater=False,
        ),
        Field(
            "type",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            default="periodic",
        ),
        Field(
            "interval",
            type=SecondsDeltaType,
            creation_parameter=True,
            optional=True,
        ),
        Field(
            "day_of_week",
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "time_of_day",
            type=TimeOfDayType,
            creation_parameter=True,
            optional=True,
        ),
        Field(
            "retention",
            type=SecondsDeltaType,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "lock_snapshots",
            type=bool,
            mutable=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
        ),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_snapshot_policies()

    @classmethod
    def get_plural_name(cls):
        return "schedules"

    def disable(self):
        """
        Disables the schedule for when to
        create snapshots
        """
        url = self.get_this_url_path().add_path("disable")
        return self.system.api.post(url)

    def enable(self):
        """
        Enables the schedule for when to
        create snapshots
        """
        url = self.get_this_url_path().add_path("enable")
        return self.system.api.post(url)
