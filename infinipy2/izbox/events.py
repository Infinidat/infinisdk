import collections
from itertools import count

from ..core import Field, SystemObject, TypeBinder
from ..core.api.special_values import Autogenerate
from ..core.system_object_utils import make_getter_updater


default_event_page_size = 1000
default_max_events = 10 ** 6
max_events_page_size = 1000

class Events(TypeBinder):
    def __init__(self, system):
        super(Events, self).__init__(Event, system)

    def get_events(self, min_event_id=0):
        return list(self.find(Event.fields.id>=min_event_id).sort(Event.fields.id))

    def get_last_events(self, num, reversed=False):
        return list(self.find().sort(-Event.fields.id).page_size(num).page(1))

    def get_last_event(self):
        return self.get_last_events(1)[0]

    def _get_events_query(self, query="", page_size=None, max_events=default_max_events):
        assert max_events > 0, "max_events must be a positive integer"
        if page_size is None:
            page_size = min(max_events_page_size, max_events)
        if query:
            query = query + '&'
        query = "events?{query}page_size={page_size}&".format(query=query, page_size=page_size) + "page={page}"
        returned = []
        page_counter = count(1)
        while len(returned) < max_events:
            events = [self._build_event(e) for e in self.system.api.get(query.format(page=page_counter.next())).get_result()]
            if events:
                returned.extend(events)
            else:
                break
        del returned[max_events:]
        return returned

    def get_custom_events_query(self, query="", **kwargs):
        return self._get_events_query(query, **kwargs)

    def _get_events_types(self):
        return self.system.api.get("events/types").get_result()
    def get_codes(self):
        return self._get_events_types()['codes']
    def get_codes_list(self):
        return [e['code'] for e in self.get_codes()]
    def get_codes_description_list(self):
        return [e['description'] for e in self.get_codes()]
    def get_levels(self):
        return self._get_events_types()['levels']
    def get_visibilities(self):
        return self._get_events_types()['visibilities']
    def get_reporters(self):
        return self._get_events_types()['reporters']

    def _build_event(self, event_dict):
        return event_dict

    def create_custom_event(self, level='INFO', description='custom event description', data=None):
        if data is None:
            data = dict()
        return self.system.api.post("events/custom", data={"data": data, "level": level, "description": description}).get_result()

    def get_event_by_uuid(self, uuid):
        result = self.get_custom_events_query("uuid=eq:{}".format(uuid))
        if result:
            return result[0]

class Event(SystemObject):

    FIELDS = [
        Field("id", type=int, is_identity=True),
    ]

    BINDER_CLASS = Events

    def __getitem__(self, item):
        return self._cache[item]

    def __contains__(self, field_name):
        return field_name in self._cache

    def __iter__(self):
        return iter(self._cache)

    def __len__(self):
        return len(self._cache)

    def keys(self):
        return self._cache.keys()

collections.Mapping.register(Event)

class PushRule(SystemObject):

    URL_PATH = "/api/rest/events/push_rules"

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("visibility", mandatory=True, default="CUSTOMER"),
        Field("filters", mandatory=True, default=list),
        Field("recipients", mandatory=True, default=list),
        Field("name", mandatory=True, default=Autogenerate("rule_{timestamp}")),
    ]

    get_name, update_name = make_getter_updater("name")
