from infinipy2.core.exceptions import APICommandFailed
from ..utils import TestCase

class APITest(TestCase):

    def test_relative_api(self):
        self.system.api.get("system")

    def test_absolute_api(self):
        self.system.api.get("/api/rest/system")

    def test_specific_address(self):
        with self.assertRaises(APICommandFailed) as caught:
            self.system.api.get("/api/rest/system", address=self.simulator.get_inactive_node_address())
