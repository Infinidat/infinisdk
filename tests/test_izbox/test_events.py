from infinipy2._compat import xrange
from ..utils import TestCase
import forge

class EventsTest(TestCase):

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

    def test_create_custom_event(self):
        description = 'test events'
        event_from_post = self.system.events.create_custom_event(description=description)
        event_from_list = self.system.events.get_last_events(1)[0].get_fields()
        self.assertEquals(event_from_list['description'], description)
        self.assertEquals(event_from_list['code'], "CUSTOM_EVENT_INFO")

    def test_create_custom_event_with_data(self):
        description = 'test events - {param}'
        data=dict(param=10)
        event_from_post = self.system.events.create_custom_event(description=description, data=data)
        actual_data=event_from_post['data'][0]
        self.assertEquals(actual_data['name'], 'param')
        self.assertEquals(actual_data['value'], 10)
        self.assertIn(actual_data['type'], 'int')



    def test_get_event_by_uuid(self):
        custom_event = self.system.events.create_custom_event(description='test event')
        event = self.system.events.get_event_by_uuid(custom_event['uuid'])
        self.assertEquals(event['uuid'], custom_event['uuid'])

    def test_event_fields_operators(self):
        for index in xrange(5):
            custom_event = self.system.events.create_custom_event(description='test event')
        event = self.system.events.get_last_event()

        self.assertEquals(event['uuid'], custom_event['uuid'])  # Test: get_last_event & __getitem__
        self.assertTrue('uuid' in event)  # Test: __contains__
        self.assertFalse('fake_field_name' in event)  # Test: __contains__
        keys = event.keys()
        self.assertTrue(len(event), len(keys))  # Test: __len__
        self.assertEqual(set(keys), set(k for k in event))  # test __iter__

    def test_codes(self):
        codes = self.system.events.get_codes()
        self.assertTrue(len(codes) > 0)

        codes_list = self.system.events.get_codes_list()
        self.assertTrue(any('USER_CREATED'==code for code in codes_list))

    def test_get_levels(self):
        self.assertEqual(self.system.events.get_levels(),
                         ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    def test_get_codes_description_list(self):
        codes_description_list = self.system.events.get_codes_description_list()
        self.assertTrue(len(codes_description_list) > 0)

    def test_get_visibilities(self):
        self.assertEqual(self.system.events.get_visibilities(),
                         ['CUSTOMER', 'INFINIDAT'])

    def test_get_reporters(self):
        self.assertTrue('CORE' in self.system.events.get_reporters())


class EventsTestsWithForge(TestCase):
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
