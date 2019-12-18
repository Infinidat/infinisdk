import gossip
from urlobject import URLObject as URL

from ..core import Field
from ..core.api.special_values import Autogenerate
from ..core.object_query import PolymorphicQuery
from ..core.translators_and_types import MillisecondsDatetimeType
from ..core.utils import end_reraise_context
from ..core.type_binder import TypeBinder
from .system_object import InfiniBoxObject


class QosPolicyBinder(TypeBinder):
    def is_enabled(self):
        res = self.system.api.get("qos/state")
        return res.get_result()["is_enabled"]

    def enable(self):
        return self.system.api.post("qos/enable", data={})

    def get_assigned_entities(self):
        return QosPolicy._get_assigned_entities_query(self.system, URL("qos/assigned_entities")) # pylint: disable=protected-access


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

    BINDER_CLASS = QosPolicyBinder

    @classmethod
    def _get_assigned_entities_query(cls, system, url):
        def object_factory(system, received_item):
            type_name = received_item['entity_type'].lower()
            entity_id = received_item['entity_id']
            return system.objects.get_binder_by_type_name(type_name).get_by_id_lazy(entity_id)

        object_types = (system.volumes.object_type, system.filesystems.object_type,
                        system.pools.object_type)

        return PolymorphicQuery(system, url, object_types, object_factory)

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
        """Returns the assigned entities of this QOS policy"""
        return self._get_assigned_entities_query(self.system, self.get_this_url_path().add_path('assigned_entities'))

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
