from datetime import timedelta
from itertools import izip_longest

import arrow
import flux
from munch import Munch

from urlobject import URLObject


_METRICS_URL = URLObject('/api/rest/metrics')


class Metrics(object):
    """Manages various actions needed for metric colllection
    """

    def __init__(self, system):
        super(Metrics, self).__init__()
        self.system = system

    def create_filter(self, **fields):
        """Creates a new filter for collecting metrics.

        :return: a :class:`.Filter` object
        """
        resp = self.system.api.post(
            _METRICS_URL.add_path('filters'), data=fields)
        return Filter(self.system, resp.get_result()['id'])

    def get_available_fields(self):
        resp = self.system.api.get(_METRICS_URL.add_path('available_fields'))
        return [
            TopLevelField.from_json(field)
            for field in resp.get_result()['available_filter_fields']
        ]

    def get_samples(self, collectors):
        """Retrieves all pending samples for a group of collectors
        """
        returned = []
        collectors_by_id = {c.id: c for c in collectors}
        path = _METRICS_URL.add_path('collectors/data')
        path = path.set_query_param('collector_id', 'in:{}'.format(
            ','.join(str(c.id) for c in collectors)))
        resp = self.system.api.get(path).get_result()
        for collector_data in resp['collectors']:
            collector = collectors_by_id[collector_data['id']]
            interval = collector_data['interval_milliseconds'] / 1000.0
            end_timestamp = arrow.Arrow.fromtimestamp(
                collector_data['end_timestamp_milliseconds'] / 1000.0)

            series = collector_data['data']
            for index, sample in enumerate(series):
                timestamp = end_timestamp - \
                            timedelta(seconds=interval * (len(series) - index + 1))
                returned.append(Sample(collector, sample, timestamp, interval))

        return returned


class TopLevelField(object):

    def __init__(self, name, values):
        super(TopLevelField, self).__init__()
        self.name = name
        self.values = values

    @classmethod
    def from_json(cls, j):
        return cls(name=j['name'], values=j['values'])


class Filter(object):
    """Represents a single filter defined on the system for metric gathering
    """

    def __init__(self, system, id):
        super(Filter, self).__init__()
        self.system = system
        self.id = id
        available_fields = self.system.api.get(
            self.get_this_url_path().add_path('available_fields')).get_result()
        #: munch of :class:`.FilterField` objects describing the filter fields of this filter
        self.filter_fields = Munch({info['name']: FilterField(
            info) for info in available_fields['available_filter_fields']})
        #: munch of :class:`.CollectorField` objects describing the collector fields of this filter
        self.collector_fields = Munch({info['name']: CollectorField(
            info) for info in available_fields['available_collector_fields']})

    def update(self, **fields):
        """Updates the filter according to the specified fields
        """
        self.system.api.put(self.get_this_url_path(), data=fields)

    def create_collector(self, collected_fields, type='COUNTER'):
        """Creates a collector from this filter
        """
        resp = self.system.api.post(_METRICS_URL.add_path('collectors'), data={
            'collected_fields': collected_fields,
            'type': type,
            'filter_id': self.id})

        return Collector(self.system, self, collected_fields, resp.get_result()['id'])

    def get_this_url_path(self):
        return _METRICS_URL.add_path('filters').add_path(str(self.id))

    def delete(self):
        """Deletes this filter
        """
        self.system.api.delete(self.get_this_url_path())


class FilterField(object):

    def __init__(self, info):
        super(FilterField, self).__init__()
        #: name of the field
        self.name = info['name']
        #: type of the filter field
        self.type = info['type']
        #: possible filter values
        self.values = info.get('values', None)
        if self.values is not None:
            self.values = set(self.values)

    def __repr__(self):
        return '<{0.__class__.__name__} {0.name}>'.format(self)


class CollectorField(object):

    def __init__(self, info):
        super(CollectorField, self).__init__()
        #: description of this filter field
        self.description = info['description']
        #: name of this field
        self.name = info['name']
        #: Unit of measurement
        self.unit = info['unit']
        if self.unit.lower() == 'n/a':
            self.unit = None

    def __repr__(self):
        return '<{0.__class__.__name__} {0.name}>'.format(self)


class Collector(object):
    """Represents a single collector that can be polled for data
    """

    def __init__(self, system, filter, field_names, id):
        super(Collector, self).__init__()
        self.system = system
        self.filter = filter
        self.field_names = field_names
        self.id = id

    def get_sample(self):
        """Get a single sample from the collector
        :returns: a :class:`.Sample` object
        """
        return next(self.iter_samples())

    def get_samples(self):
        """Get all samples which are ready for collection
        :returns: a list of :class:`.Sample` objects
        """
        return self.system.metrics.get_samples([self])

    def iter_samples(self):
        """Iterates the collector, getting samples indefinitely

        yields :class:`.Sample` object, each time waiting for them to be emitted
        """

        next_sample_time = None

        while True:
            if next_sample_time is not None and next_sample_time > flux.current_timeline.time():
                flux.current_timeline.sleep(
                    max(0, next_sample_time - flux.current_timeline.time()))
            samples = self.get_samples()
            for sample in samples:
                yield sample
                next_sample_time = sample.timestamp.timestamp + sample.interval

    def delete(self):
        """Deletes this collector
        """
        self.system.api.delete(self.get_this_url_path())

    def get_this_url_path(self):
        return _METRICS_URL.add_path('collectors').add_path(str(self.id))


class Sample(object):

    def __init__(self, collector, values, timestamp, interval):
        super(Sample, self).__init__()
        self.collector = collector
        #: the values for this sample, as an ordered Python list
        self.value_list = values
        #: Munch mapping the field name to its respective sample
        self.values = Munch(izip_longest(collector.field_names, values))
        #: a timestamp (Arrow) object of when this sample was taken
        self.timestamp = timestamp
        #: the interval, in seconds, until the next sample
        self.interval = interval

    @property
    def value(self):
        if len(self.values) > 1:
            raise RuntimeError(
                'Multiple values received. Cannot fetch single sample value')

        return self.value_list[0]

    def __repr__(self):
        return '[{}: {}]'.format(self.timestamp, self._get_sample_string())

    def _get_sample_string(self):
        returned = []
        for value_name, value in self.values.items():
            item = '{}: {}'.format(value_name, value)
            unit = self.collector.filter.collector_fields[value_name].unit
            if unit:
                item += unit
            returned.append(item)
        return ', '.join(returned)
