from urlobject import URLObject as URL
from ..core.bindings import RelatedObjectBinding
from ..core import Field, SystemObject


class NotificationRule(SystemObject):


    URL_PATH = URL('/api/rest/notifications/rules')

    FIELDS = [
        Field('id', type=int, is_identity=True),
        Field('name', mutable=True),
        Field('event_code', type=str),
        Field('event_level', type=list),
        Field('target_parameters', type=dict),
        Field('target', api_name='target_id', binding=RelatedObjectBinding('notification_targets')),
        Field('include_events', type=list),
        Field('exclude_events', type=list),
        Field('event_visibility', type=list),
    ]

    @classmethod
    def get_type_name(cls):
        return 'notification_rule'
