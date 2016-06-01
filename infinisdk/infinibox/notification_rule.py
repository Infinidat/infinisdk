from urlobject import URLObject as URL
from ..core.utils import DONT_CARE
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

    def does_match_event(self, event, from_cache=DONT_CARE):
        if event.get_visibility() == 'INFINIDAT' and event.get_visibility() != self.get_target(from_cache=from_cache).get_visibility(from_cache=from_cache):
            return False

        if self.get_event_code(from_cache=from_cache) is not None and self.get_event_code(from_cache=from_cache) == event.get_code():
            return True

        if event.get_code() in self.get_include_events(from_cache=from_cache):
            return True
        
        return (event.get_visibility() in self.get_event_visibility(from_cache=from_cache) and
                event.get_level() in self.get_event_level(from_cache=from_cache) and
                event.get_code() not in self.get_exclude_events(from_cache=from_cache))
