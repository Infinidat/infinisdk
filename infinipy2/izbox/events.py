import collections

from ..core import Field, SystemObject, TypeBinder
from ..core.api.special_values import Autogenerate


default_event_page_size = 1000
default_max_events = 10 ** 6
max_events_page_size = 1000

class Events(TypeBinder):
    def __init__(self, system):
        super(Events, self).__init__(Event, system)
        self._types = None

    def get_events(self, min_event_id=0):
        return list(self.find(Event.fields.id >= min_event_id).sort(Event.fields.id))

    def get_last_events(self, num, reversed=False):
        returned = list(self.find().sort(-Event.fields.id).page_size(num).page(1))
        if not reversed:
            returned.reverse()
        return returned

    def get_last_event(self):
        return self.get_last_events(1)[0]

    def _get_events_types_from_system(self):
        return self.system.api.get("events/types").get_result()

    def _get_events_types(self):
        if self._types is None:
            self._types = self._get_events_types_from_system()
        return self._types.copy()

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

    def create_custom_event(self, level='INFO', description='custom event description', visibility='CUSTOMER', data=None):
        if data is None:
            data = dict()
        return self.system.api.post("events/custom", data={"data": data, "level": level, "description": description, "visibility":visibility}).get_result()

    def get_event_by_uuid(self, uuid):
        result = list(self.find(uuid=uuid))
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
        Field("visibility", creation_parameter=True, mutable=True, default="CUSTOMER"),
        Field("filters", creation_parameter=True, mutable=True, default=list),
        Field("recipients", creation_parameter=True, mutable=True, default=list),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("rule_{timestamp}")),
    ]
