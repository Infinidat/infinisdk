from infinipy2.core.api import APITarget, API
from ..utils import TestCase
from ..utils import api_scenario
from ..utils import FakeSystem

class APITest(TestCase):

    def setUp(self):
        super(APITest, self).setUp()
        self.system = FakeSystem()

    def test_api(self):
        with api_scenario('izbox_handshake', self.system):
            self.system.api.get("system")
