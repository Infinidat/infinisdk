###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
import collections

from ..core import Field, SystemObject, TypeBinder


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
        events = self.get_last_events(1)
        if len(events) > 0:
            return events[0]
        return None

    def _get_events_types_from_system(self):
        return self.system.api.get("events/types").get_result()

    def _get_events_types(self):
        if self._types is None:
            self._types = self._get_events_types_from_system()
        return self._types.copy()

    def get_codes(self):
        return self._get_events_types()['codes']

    def get_visibilities(self):
        return self._get_events_types()['visibilities']

    def get_reporters(self):
        return self._get_events_types()['reporters']


class Event(SystemObject):

    FIELDS = [
        Field("id", type=int, cached=True, is_identity=True, is_sortable=True, is_filterable=True),
        Field("level", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field("code", type=str, cached=True),
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

    def get_field(self, field_name, from_cache=True, fetch_if_not_cached=True):
        return super(Event, self).get_field(field_name, from_cache, fetch_if_not_cached)

    def get_fields(self, field_names=(), from_cache=True, fetch_if_not_cached=True):
        return super(Event, self).get_fields(field_names, from_cache, fetch_if_not_cached)

collections.Mapping.register(Event)
