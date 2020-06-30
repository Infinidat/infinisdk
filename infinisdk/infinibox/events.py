import gossip
from arrow import Arrow
from ..core import Events as EventsBase
from ..core.api.special_values import OMIT
from ..core.translators_and_types import MillisecondsDatetimeTranslator
from ..core.utils import normalized_query_value, end_reraise_context


class Events(EventsBase):

    def create_custom_event(self, level='INFO', description='custom event', visibility='CUSTOMER', data=None):
        _data = {"data": data or [],
                 "level": level,
                 "description_template": description,
                 "visibility":visibility}
        object_data = self.system.api.post("events/custom", data=_data).get_result()
        return self.object_type(self.system, object_data)

    def get_levels(self):
        sorted_levels = sorted(self.get_events_types()['levels'], key=lambda d: d['value'])
        return [level_info['name'] for level_info in sorted_levels]

    def get_levels_name_to_number_mapping(self):
        return dict((level_info['name'], level_info['value']) for level_info in self.get_events_types()['levels'])

    def _get_anti_flooding_path(self):
        return "config/mgmt/events.flooding_detector.enabled"

    def is_anti_flooding_enabled(self):
        return self.system.api.get(self._get_anti_flooding_path()).get_result()

    def disable_anti_flooding(self):
        self.system.api.put(self._get_anti_flooding_path(), data=False)

    def enable_anti_flooding(self):
        self.system.api.put(self._get_anti_flooding_path(), data=True)

    def delete(self, *, retention):
        hook_tags = self.object_type.get_tags_for_object_operations(self.system)
        url = self.get_url_path()
        if retention is not OMIT:
            if isinstance(retention, Arrow):
                retention = MillisecondsDatetimeTranslator().to_api(retention)
            retention = normalized_query_value(retention)
            url = url.add_query_param("timestamp", "le:{}".format(retention))
        gossip.trigger_with_tags('infinidat.sdk.pre_event_retention', {'system': self.system, 'retention': retention},
                                 tags=hook_tags)
        try:
            self.system.api.delete(url)
        except Exception as e:       # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.event_retention_failure',
                                         {'retention': retention, 'exception': e, 'system': self.system},
                                         tags=hook_tags)
        gossip.trigger_with_tags('infinidat.sdk.post_event_retention', {'system': self.system, 'retention': retention},
                                 tags=hook_tags)
