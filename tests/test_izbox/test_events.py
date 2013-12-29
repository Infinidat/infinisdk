from infinipy2._compat import xrange
from ..utils import IZBoxTestCase

class EventsTest(IZBoxTestCase):

    def test_create_custom_event(self):
        description = 'test events'
        event_from_post = self.system.events.create_custom_event(description=description)
        event_from_list = self.system.events.get_last_events(1)[0].get_fields()
        self.assertEquals(event_from_post['description'], description)
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

    def test_get_codes_description_list(self):
        codes_description_list = self.system.events.get_codes_description_list()
        self.assertTrue(len(codes_description_list) > 0)
