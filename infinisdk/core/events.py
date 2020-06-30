import collections
from ..core.q import Q
from ..core import Field, SystemObject, TypeBinder, MillisecondsDatetimeType
from ..core.bindings import RelatedObjectBinding


class Events(TypeBinder):
    def __init__(self, system):
        super(Events, self).__init__(Event, system)
        self._types = None

    def get_events(self, min_event_id=0):
        return self.find(Event.fields.id >= min_event_id).sort(Q.id).to_list()

    def get_last_events(self, num, reversed=False):  # pylint: disable=redefined-builtin
        returned = self.find().sort(-Q.id).page_size(num).page(1).to_list()
        if not reversed:
            returned.reverse()
        return returned

    def get_first_events(self, num):
        returned = self.find().sort(+Q.id).page_size(num).page(1).to_list()
        return returned

    def get_last_event(self):
        events = self.get_last_events(1)
        if len(events) > 0:
            return events[0]
        return None

    def _get_events_types_from_system(self):
        return self.system.api.get("events/types").get_result()

    def get_events_types(self):
        if self._types is None:
            self._types = self._get_events_types_from_system()
        return self._types.copy()

    def get_codes(self):
        return self.get_events_types()['codes']

    def get_visibilities(self):
        return self.get_events_types()['visibilities']

    def get_reporters(self):
        return self.get_events_types()['reporters']


class Event(SystemObject):

    FIELDS = [
        Field("id", type=int, cached=True, is_identity=True, is_sortable=True, is_filterable=True),
        Field("code", type=str, cached=True, is_filterable=True, is_sortable=True, use_in_repr=True),
        Field("level", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field("username", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field("description", type=str, cached=True),
        Field("timestamp", type=MillisecondsDatetimeType, cached=True, is_filterable=True, is_sortable=True),
        Field("reporter", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field("visibility", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field("system_version", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field("source_node_id", type=int, cached=True, is_filterable=True, is_sortable=True),
        Field("description_template", type=str, cached=True),
        Field("affected_entity_id", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field("tenant", api_name="tenant_id", binding=RelatedObjectBinding('tenants'),
              type='infinisdk.infinibox.tenant:Tenant', feature_name='tenants',
              is_filterable=True, is_sortable=True),
    ]

    BINDER_CLASS = Events

    def get_binder(self):
        return self.system.events

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

    def get_event_data_dict(self):
        return dict((value['name'], value['value']) for value in self.get_field('data', from_cache=True))

collections.abc.Mapping.register(Event)  # pylint: disable=no-member
