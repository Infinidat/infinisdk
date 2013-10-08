from ..utils import TestCase

class APITest(TestCase):
    API_SCENARIOS = ["izbox_queries"]

    def test_api(self):
        self.system.api.get("system")
