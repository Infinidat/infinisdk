from infinipy2.core.api import OMIT
from infinipy2.core.exceptions import APICommandFailed
from infinipy2.core.api import Autogenerate

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

    def test_autogenerate_fields(self):
        responses = [
            self.system.api.post(
                "/api/izsim/echo_post",
                data={"a":
                      {"b":
                       {"name": Autogenerate("obj-{ordinal}-{time}-{timestamp}-{uuid}")}}})
            for i in range(2)]
        jsons = [r.get_result() for r in responses]
        for index, json in enumerate(jsons):
            name = json["a"]["b"]["name"]
            obj, ordinal, time, timestamp, uuid = name.split("-")
            self.assertEquals(int(ordinal) - 1, index)
            self.assertEquals(int(timestamp) // 1000, int(float(time)))
            self.assertTrue(uuid)
            self.assertGreater(len(set(uuid)), 1, "uuid consists of only one character")

    def test_specific_address(self):
        with self.assertRaises(APICommandFailed) as caught:
            self.system.api.get("/api/rest/system", address=self.simulator.get_inactive_node_address())

    def test_specific_address_doesnt_change_active_url(self):
        self.system.api.get("/api/rest/system")
        active_url = self.system.api._active_url
        new_url = self.system.api._active_url = "http://blap.com/a/b/c"
        self.system.api.get("/api/rest/system", address=self.simulator.get_active_node_address())
        self.assertEquals(self.system.api._active_url, new_url)
