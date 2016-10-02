from urlobject import URLObject as URL
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from ..core import Field, SystemObject


class NotificationRule(SystemObject):


    URL_PATH = URL('/api/rest/notifications/rules')

    FIELDS = [
        Field('id', type=int, is_identity=True),
        Field('name', mutable=True, creation_parameter=True, default=Autogenerate("rule_{uuid}")),
        Field('event_code', type=str, mutable=True),
        Field('event_level', type=list, mutable=True),
        Field('target_parameters', type=dict, mutable=True),
        Field('target', api_name='target_id', mutable=True, creation_parameter=True,
              binding=RelatedObjectBinding('notification_targets')),
        Field('include_events', type=list, mutable=True),
        Field('exclude_events', type=list, mutable=True),
        Field('event_visibility', type=list),
    ]

    @classmethod
    def get_type_name(cls):
        return 'notification_rule'
