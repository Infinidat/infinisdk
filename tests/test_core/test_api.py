from infinipy2.izbox import IZBox
from ..utils import TestCase
from ..utils import api_scenario

class APITest(TestCase):

    def setUp(self):
        super(APITest, self).setUp()
        self.system = IZBox(("address", 80))

    def test_api(self):
        with api_scenario(self.system, 'izbox_handshake'):
            self.system.api.get("system")
