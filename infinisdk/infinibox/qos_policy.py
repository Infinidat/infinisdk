from urlobject import URLObject as URL

from ..core import Field
from ..core.api.special_values import Autogenerate
from ..core.object_query import PolymorphicQuery
from ..core.translators_and_types import MillisecondsDatetimeType
from .system_object import InfiniBoxObject


class QosPolicy(InfiniBoxObject):
    URL_PATH = URL("/api/rest/qos/policies")
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("qos_{uuid}")),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("type", creation_parameter=True, mutable=True, is_filterable=True),
        Field("max_ops", type=int, creation_parameter=True, mutable=True, optional=True, is_filterable=True,
              is_sortable=True),
        Field("max_bps", type=int, creation_parameter=True, mutable=True, optional=True, is_filterable=True,
              is_sortable=True),
        Field("burst_enabled", type=bool, creation_parameter=True, optional=True, is_filterable=True, is_sortable=True),
        Field("burst_factor", type=float, creation_parameter=True, mutable=True, optional=True, is_filterable=True,
              is_sortable=True),
        Field("burst_duration_seconds", type=int, creation_parameter=True, mutable=True, optional=True,
              is_filterable=True, is_sortable=True),
    ]

    @classmethod
    def get_type_name(cls):
        return "qos_policy"

    @classmethod
    def get_plural_name(cls):
        return "qos_policies"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_qos()

    def get_assigned_entities(self):
        def object_factory(system, received_item):
            type_name = received_item['entity_type'].lower()
            return system.objects.get_binder_by_type_name(type_name).object_type.construct(system, received_item)

        object_types = (self.system.volumes.object_type, self.system.filesystems.object_type,
                        self.system.pools.object_type)
        return PolymorphicQuery(self.system, self.get_this_url_path().add_path('assigned_entities'),
                                object_types, object_factory)

    def assign_entity(self, entity):
        data = {'entity_id': entity.id, 'entity_type': entity.get_type_name()}
        self.system.api.post(self.get_this_url_path().add_path('assigned_entities'), data=data)

    def unassign_entity(self, entity):
        self.system.api.post(self.get_this_url_path().add_path('unassign'),
                             data={'entity_id': entity.id})
