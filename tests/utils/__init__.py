import infi.unittest
from .api_scenarios import api_scenario
from infinipy2.izbox import IZBox

class TestCase(infi.unittest.TestCase):
    API_SCENARIOS = None
    SYSTEM_CLASS = IZBox

    def setUp(self):
        super(TestCase, self).setUp()
        if self.API_SCENARIOS:
            self.system = self.SYSTEM_CLASS(("address", 80))
            self.scenario = api_scenario(self.system, *self.API_SCENARIOS)
            self.scenario.start()
            self.addCleanup(self.scenario.end)
