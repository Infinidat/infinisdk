from infinipy2.core.api import OMIT
from infinipy2.core.exceptions import APICommandFailed, APITransportFailure
from infinipy2.core.api import Autogenerate
import requests

from ..utils import CoreTestCase, IZBoxTestCase

class APITestWithIZSim(IZBoxTestCase):

    def test_omit_fields(self):
        resp = self.system.api.post("/api/izsim/echo_post", data={"a": "b"})
        self.assertEquals(resp.get_result(), {"a": "b"})

        resp = self.system.api.post("/api/izsim/echo_post", data={"a": "b", "c": {"d": {"e": OMIT}}})
        self.assertEquals(resp.get_result(), {"a": "b", "c": {"d": {}}})

    def test_error_response(self):
        with self.assertRaises(APICommandFailed) as caught:
            self.system.api.post("/api/izsim/echo_error", data={'a':1})

        exception_response = caught.exception.response
        self.assertIs(exception_response.get_error(), None)

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

    def test_api_transport_error(self):
        def fake_request(api_obj, *args, **kwargs):
            raise requests.exceptions.ConnectionError('FakeConnectionError')
        def set_request(new_request):
            curr_val = self.system.api._request
            self.system.api._request = new_request
            return curr_val

        orig_request = set_request(fake_request)
        self.addCleanup(lambda: set_request(orig_request))

        with self.assertRaises(APITransportFailure):
            self.system.api.post("/api/izsim/echo_post")


class APITest(CoreTestCase):

    def test_relative_api(self):
        self.system.api.get("system")

    def test_absolute_api(self):
        self.system.api.get("/api/rest/system")
    def test_normalize_addresses(self):
        get_normalized = self.system._normalize_addresses
        self.assertEqual(get_normalized('1.2.3.4'), [('1.2.3.4', 80)])

        with self.assertRaises(ValueError):
            get_normalized(('1.2.3.4', 80, 20))

    def test_approval_context(self):
        with self.system.api.get_unapproved_context():
            self.assertFalse(self.system.api._approved)

            with self.system.api.get_approved_context():
                self.assertTrue(self.system.api._approved)

            self.assertFalse(self.system.api._approved)
