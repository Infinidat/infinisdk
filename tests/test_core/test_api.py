from infinipy2.core.api import APITarget, API
from ..utils import TestCase
from ..utils import api_scenario

class APITest(TestCase):

    def setUp(self):
        super(APITest, self).setUp()
        self.target = FakeTarget()
        self.api = API(self.target)

    def test_api(self):
        with api_scenario('izbox_handshake', self.target):
            self.api.get("system")

class FakeTarget(APITarget):
    _ADDRESS = ("fakeaddress", 80)
    _AUTH = ("fakeuser", "fakepassword")

    def get_api_timeout(self):
        return 1

    def get_api_address(self):
        return self._ADDRESS

    def get_api_auth(self):
        return self._AUTH
