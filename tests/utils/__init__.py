import infi.unittest
from infinipy2.izbox import IZBox
from izsim import Simulator

class TestCase(infi.unittest.TestCase):
    API_SCENARIOS = None
    SYSTEM_CLASS = IZBox

    def setUp(self):
        super(TestCase, self).setUp()
        self.simulator = Simulator()
        self.simulator.start_context()
        self.addCleanup(self.simulator.end_context)
        self.system = IZBox(self.simulator.get_address())
