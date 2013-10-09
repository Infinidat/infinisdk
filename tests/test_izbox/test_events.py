from ..utils import TestCase

class EventsTest(TestCase):
    API_SCENARIOS = ["izbox_events"]

    def test_get_last_events(self):
        events = self.system.events.get_last_events(2)
        self.assertEquals(len(events), 2)
