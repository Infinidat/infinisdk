from infinipy2._compat import xrange
from ..utils import CoreTestCase
import forge

class EventsTest(CoreTestCase):

    def test_get_last_events(self):
        events = self.system.events.get_last_events(1)
        self.assertEquals(len(events), 1)

    def test_get_last_events_with_reversed_param(self):
        # Ensuring that there are at least 2 events
        event1 = self.system.events.create_custom_event(description='Custom 1')
        event2 = self.system.events.create_custom_event(description='Custom 2')

        regular_events = self.system.events.get_last_events(2, False)
        reversed_events = self.system.events.get_last_events(2, True)

        self.assertEquals(len(regular_events), 2)
        self.assertEquals(len(reversed_events), 2)
        self.assertEquals(event1['id'], regular_events[0].id)
        self.assertEquals(event2['id'], regular_events[1].id)
        self.assertEquals(regular_events[0], reversed_events[1])
        self.assertEquals(regular_events[1], reversed_events[0])

    def test_get_events(self):
        custom_event = self.system.events.create_custom_event(description='')
        events = self.system.events.get_events(min_event_id=custom_event['id']+1)
        self.assertEqual(len(events), 0)

        events = self.system.events.get_events(min_event_id=custom_event['id'])
        self.assertEqual(len(events), 1)

    def test_get_levels(self):
        self.assertTrue('CRITICAL' in self.system.events.get_levels())

    def test_get_visibilities(self):
        expected = set(['CUSTOMER', 'INFINIDAT'])
        self.assertEqual(set(self.system.events.get_visibilities()), expected)

    def test_get_reporters(self):
        self.assertTrue(len(self.system.events.get_reporters()) > 0)

    def test_between_operator(self):
        min_id, max_id = 1, 3
        id_field = self.system.events.fields.get('id')
        id_filter = id_field.__between__((min_id, max_id))
        events = list(self.system.events.find(id_filter))

        range_validator = lambda event: event.id <= max_id and event.id >= min_id

        self.assertLessEqual(len(events), (max_id - min_id + 1))
        self.assertTrue(all(map(range_validator, events)))

    def test_complex_queries(self):
        min_index, max_index = 1, 2
        events = [self.system.events.create_custom_event() for i in xrange(5)]

        id_field = self.system.events.fields.get('id')
        id_range = (events[min_index]['id'], events[max_index]['id'])
        id_filter = id_field.__between__(id_range)

        Event = self.system.events.object_type
        kwargs = dict(level=events[0]['level'],
                      reporter=events[0]['reporter'],
                      code=events[0]['code'])
        filtered_events = self.system.events.find(id_filter, **kwargs)
        results = list(filtered_events.sort(-Event.fields.id))

        self.assertEqual(len(results), (max_index - min_index + 1))
        self.assertEqual(events[min_index]['id'], results[-1].id)
        self.assertEqual(events[max_index]['id'], results[0].id)


class EventsTestsWithForge(CoreTestCase):
    def setUp(self):
        super(EventsTestsWithForge, self).setUp()
        self.forge = forge.Forge()

    def tearDown(self):
        self.forge.verify()
        self.forge.restore_all_replacements()
        self.forge.reset()
        super(EventsTestsWithForge, self).tearDown()

    def test_events_types_caching(self):
        mock = self.forge.replace(self.system.events, '_get_events_types_from_system')
        mock().and_return({'codes': [], 'levels':[]})
        self.forge.replay()

        self.assertIs(self.system.events._types, None)
        self.system.events.get_codes()

        self.assertIsNot(self.system.events._types, None)
        self.system.events.get_codes()
        self.system.events.get_levels()
