from ..utils import TestCase

class EventsTest(TestCase):

    def test_get_last_events(self):
        events = self.system.events.get_last_events(1)
        self.assertEquals(len(events), 1)

    def test_create_custom_event(self):
        description = 'test events'
        event_from_post = self.system.events.create_custom_event(description=description)
        event_from_list = self.system.events.get_last_events(1)[0].get_fields()
        self.assertEquals(event_from_list['description'], description)
        self.assertEquals(event_from_list['code'], "CUSTOM_EVENT_INFO")
