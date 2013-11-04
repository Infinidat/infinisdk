from ..utils import TestCase
from infinipy2.izbox import IZBox
from infinipy2.core.exceptions import APICommandFailed

class ActiveNodeDetectionFailureTest(TestCase):

    def test_fails_if_no_alternative_node(self):
        system = IZBox(self.simulator.get_inactive_node_address())
        with self.assertRaises(APICommandFailed):
            system.api.get("system")


class ActiveNodeDetectionTest(TestCase):

    def setUp(self):
        super(ActiveNodeDetectionTest, self).setUp()
        self.system = IZBox([self.simulator.get_inactive_node_address(), self.simulator.get_active_node_address()])

    def test_detect_active_node(self):
        api_result = self.system.api.get("system")
        self.assertEquals(api_result.url.hostname, self.simulator.active_node_url.hostname)
        self.assertEquals(api_result.url.port or 80, self.simulator.active_node_url.port or 80)
