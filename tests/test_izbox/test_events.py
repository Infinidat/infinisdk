from ..utils import TestCase

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

    def test_create_custom_event(self):
        description = 'test events'
        event_from_post = self.system.events.create_custom_event(description=description)
        event_from_list = self.system.events.get_last_events(1)[0].get_fields()
        self.assertEquals(event_from_list['description'], description)
        self.assertEquals(event_from_list['code'], "CUSTOM_EVENT_INFO")

    def test_get_event_by_uuid(self):
        custom_event = self.system.events.create_custom_event(description='test event')

        event = self.system.events.get_event_by_uuid(custom_event['uuid'])
        self.assertEquals(event['uuid'], custom_event['uuid'])
