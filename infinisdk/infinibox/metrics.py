from datetime import timedelta
from .._compat import izip_longest

import arrow
import flux
from munch import Munch
import waiting

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

    def create_collector(self, collected_fields, filters, type='COUNTER'):  # pylint: disable=redefined-builtin
        """Creates a collector from this filter
        """
        resp = self.system.api.post(_METRICS_URL.add_path('collectors'), data={
            'collected_fields': collected_fields,
            'type': type,
            'filters': filters})

        created_filter = Filter(self.system, resp.get_result()['filter_id'])
        return Collector(self.system, created_filter, collected_fields, resp.get_result()['id'], type_=type)

    def get_available_fields(self):
        resp = self.system.api.get(_METRICS_URL.add_path('available_fields'))
        return [
            TopLevelField.from_json(field)
            for field in resp.get_result()['available_filter_fields']
        ]

    def get_samples(self, collectors, wait=False, timeout=30):
        """Retrieves all pending samples for a group of collectors
        """
        returned = []

        if wait:
            iterator = waiting.iterwait(returned.__len__, timeout_seconds=timeout)
        else:
            iterator = range(1)

        for _ in iterator:
            collectors_by_id = {c.id: c for c in collectors}
            path = _METRICS_URL.add_path('collectors/data')
            path = path.set_query_param('collector_id', 'in:{}'.format(
                ','.join(str(c.id) for c in collectors)))
            resp = self.system.api.get(path).get_result()
            if resp is not None:
                collectors = resp.get('collectors', [])
                if collectors is not None:
                    for collector_data in collectors:
                        collector = collectors_by_id[collector_data['id']]
                        interval = collector_data['interval_milliseconds'] / 1000.0
                        end_timestamp = arrow.Arrow.fromtimestamp(
                            collector_data['end_timestamp_milliseconds'] / 1000.0)

                        series = collector_data['data']
                        for index, sample in enumerate(series):
                            timestamp = end_timestamp - \
                                        timedelta(seconds=interval * (len(series) - index + 1))
                            if collector_data['collector_type'] == "HISTOGRAM":
                                returned.append(HistogramSample(collector_data['histogram_field'],
                                                                collector_data['ranges'],
                                                                collector, sample, timestamp, interval))
                            elif collector_data['collector_type'] == "TOP":
                                returned.append(TopSample(collector, sample, timestamp, interval))
                            else:
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

    def __repr__(self):
        return '<Top-level field {}>'.format(self.name)


class Filter(object):
    """Represents a single filter defined on the system for metric gathering
    """

    def __init__(self, system, id):  # pylint: disable=redefined-builtin
        super(Filter, self).__init__()
        self.system = system
        self.id = id

    def get_filter_fields(self, level='BASIC'):
        """Returns a munch describing the filter fields of this filter
        """
        return self._format_fields_munch('available_filter_fields', FilterField, level)

    def get_collector_fields(self, level='BASIC'):
        """Returns a munch describing the collector fields of this filter
        """
        return self._format_fields_munch('available_collector_fields', CollectorField, level)

    def _format_fields_munch(self, name, field_class, level):
        available_fields = self.system.api.get(
            self.get_this_url_path().add_path('available_fields').set_query_param('level', level)).get_result()
        return Munch({info['name']: field_class(
            info) for info in available_fields[name]})

    def update(self, **fields):
        """Updates the filter according to the specified fields
        """
        self.system.api.put(self.get_this_url_path(), data=fields)

    def create_collector(self, collected_fields, type='COUNTER', **kwargs):  # pylint: disable=redefined-builtin
        """Creates a collector from this filter
        """
        data = {
            'collected_fields': collected_fields,
            'type': type,
            'filter_id': self.id}
        data.update(kwargs)

        resp = self.system.api.post(_METRICS_URL.add_path('collectors'), data=data)

        return Collector(self.system, self, collected_fields, resp.get_result()['id'], type_=type)

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
        self.unit = info['units'] if 'units' in info else info['unit']

        if self.unit.lower() == 'n/a':
            self.unit = None

    def __repr__(self):
        return '<{0.__class__.__name__} {0.name}>'.format(self)


class Collector(object):
    """Represents a single collector that can be polled for data
    """

    def __init__(self, system, filter, field_names, id, type_):  # pylint: disable=redefined-builtin
        super(Collector, self).__init__()
        self.system = system
        self.filter = filter
        self.field_names = field_names
        self.id = id
        self._type = type_

    def get_type(self):
        return self._type

    def get_samples(self, wait=False):
        """Get all samples which are ready for collection

        :param wait: waits until there are samples ready, meaning guaranteeing at least one sample returned

        :returns: a list of :class:`.Sample` objects
        """
        return self.system.metrics.get_samples([self], wait=wait)

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
        self.values = self._get_values()
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
            returned.append(item)
        return ', '.join(returned)

    def _get_values(self):
        return Munch(izip_longest(self.collector.field_names, self.value_list))

class HistogramSample(Sample):
    def __init__(self, histogram_field, ranges, *args):
        self.histogram_field = histogram_field
        self.ranges = ranges
        super(HistogramSample, self).__init__(*args)

    def value(self):
        return self.value_list[0]

    def __repr__(self):
        return '[{}: {}: {}]'.format(self.timestamp, self.histogram_field, self._get_sample_string())

    def _get_values(self):
        bucket_values = [Munch(izip_longest(self.collector.field_names, v)) for v in self.value_list]
        return Munch(izip_longest(self.ranges, bucket_values))

    def _get_sample_string(self):
        returned = []
        for range_, bucket in self.values.items():
            bucket_str = []
            for value_name, value in bucket.items():
                item = '{}: {}'.format(value_name, value)
                bucket_str.append(item)
            item = '{}: {}'.format(range_, bucket_str)
            returned.append(item)
        return ', '.join(returned)


class TopSample(Sample):

    def _get_values(self):
        return Munch(izip_longest(self.collector.field_names, self.value_list[0] if self.value_list else []))
