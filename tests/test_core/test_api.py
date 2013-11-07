from infinipy2.core.api import OMIT
from infinipy2.core.exceptions import APICommandFailed

from ..utils import TestCase

class APITest(TestCase):

    def test_relative_api(self):
        self.system.api.get("system")

    def test_absolute_api(self):
        self.system.api.get("/api/rest/system")

    def test_omit_fields(self):
        resp = self.system.api.post("/api/izsim/echo_post", data={"a": "b"})
        self.assertEquals(resp.get_result(), {"a": "b"})

        resp = self.system.api.post("/api/izsim/echo_post", data={"a": "b", "c": {"d": {"e": OMIT}}})
        self.assertEquals(resp.get_result(), {"a": "b", "c": {"d": {}}})

    def test_specific_address(self):
        with self.assertRaises(APICommandFailed) as caught:
            self.system.api.get("/api/rest/system", address=self.simulator.get_inactive_node_address())
