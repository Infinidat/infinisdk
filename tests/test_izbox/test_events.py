from ..utils import TestCase

class EventsTest(TestCase):

    def test_get_last_events(self):
        events = self.system.events.get_last_events(1)
        self.assertEquals(len(events), 1)
