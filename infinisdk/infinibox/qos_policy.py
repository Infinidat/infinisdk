import gossip
from urlobject import URLObject as URL

from ..core import Field
from ..core.api.special_values import Autogenerate
from ..core.object_query import PolymorphicQuery
from ..core.translators_and_types import MillisecondsDatetimeType
from ..core.utils import end_reraise_context
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
            entity_id = received_item['entity_id']
            return system.objects.get_binder_by_type_name(type_name).get_by_id_lazy(entity_id)

        object_types = (self.system.volumes.object_type, self.system.filesystems.object_type,
                        self.system.pools.object_type)
        return PolymorphicQuery(self.system, self.get_this_url_path().add_path('assigned_entities'),
                                object_types, object_factory)

    def _assign_unassign_operation(self, entity, operation_name):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.pre_qos_policy_{}'.format(operation_name),
                                 {'qos_policy': self, 'entity': entity}, tags=hook_tags)
        data = {'entity_id': entity.id}

        try:
            self.system.api.post(self.get_this_url_path().add_path(operation_name), data=data)
        except Exception as e: # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.qos_policy_{}_failure'.format(operation_name),
                                         {'exception': e, 'qos_policy': self, 'entity': entity}, tags=hook_tags)
        gossip.trigger_with_tags('infinidat.sdk.post_qos_policy_{}'.format(operation_name),
                                 {'qos_policy':self, 'entity': entity}, tags=['infinibox'])

    def assign_entity(self, entity):
        self._assign_unassign_operation(entity, 'assign')

    def unassign_entity(self, entity):
        self._assign_unassign_operation(entity, 'unassign')
