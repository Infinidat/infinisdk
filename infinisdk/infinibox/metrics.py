from datetime import timedelta
from itertools import izip_longest

import arrow
import flux
from munch import Munch


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
        resp = self.system.api.post('/api/rest/metrics/filters', data=fields)
        return Filter(self.system, resp.get_result()['id'])


class Filter(object):
    """Represents a single filter defined on the system for metric gathering
    """

    def __init__(self, system, id):
        super(Filter, self).__init__()
        self.system = system
        self.id = id
        available_fields = self.system.api.get(
            '/api/rest/metrics/filters/{}/available_fields'.format(self.id)).get_result()
        #: munch of :class:`.FilterField` objects describing the filter fields of this filter
        self.filter_fields = Munch({info['name']: FilterField(
            info) for info in available_fields['available_filter_fields']})
        #: munch of :class:`.CollectorField` objects describing the collector fields of this filter
        self.collector_fields = Munch({info['name']: CollectorField(
            info) for info in available_fields['available_collector_fields']})

    def create_collector(self, collected_fields, type='COUNTER'):
        """Creates a collector from this filter
        """
        resp = self.system.api.post('/api/rest/metrics/collectors', data={
            'collected_fields': collected_fields,
            'type': type,
            'filter_id': self.id})

        return Collector(self.system, self, collected_fields, resp.get_result()['id'])


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

    def iter_samples(self):
        """Iterates the collector, getting samples indefinitely

        yields :class:`.Sample` object, each time waiting for them to be emitted
        """

        next_sample_time = None

        while True:
            if next_sample_time is not None and next_sample_time > flux.current_timeline.time():
                flux.current_timeline.sleep(max(0, next_sample_time - flux.current_timeline.time()))
            result = self.system.api.get(
                '/api/rest/metrics/collectors/data?collector_id={}'.format(self.id)).get_result()
            [result] = [collector for collector in result[
                'collectors'] if collector['id'] == self.id]
            interval = result['interval_milliseconds'] / 1000.0
            next_sample_time = flux.current_timeline.time() + interval
            end_timestamp = arrow.Arrow.fromtimestamp(
                result['end_timestamp_milliseconds'] / 1000.0)
            series = result['data']
            if not series:
                continue
            for index, sample in enumerate(series):
                timestamp = end_timestamp - \
                    timedelta(seconds=interval *
                              (len(series) - index + 1))
                yield Sample(self, sample, timestamp)


class Sample(object):

    def __init__(self, collector, values, timestamp):
        super(Sample, self).__init__()
        self.collector = collector
        #: the values for this sample, as an ordered Python list
        self.value_list = values
        #: Munch mapping the field name to its respective sample
        self.values = Munch(izip_longest(collector.field_names, values))
        #: a timestamp (Arrow) object of when this sample was taken
        self.timestamp = timestamp

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
