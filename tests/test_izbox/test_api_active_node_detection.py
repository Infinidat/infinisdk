from ..utils import TestCase
from ..utils import api_scenario
from infinipy2.izbox import IZBox
from infinipy2.core.exceptions import APICommandFailed

class ActiveNodeDetectionFailureTest(TestCase):

    def test_fails_if_no_alternative_node(self):
        system = IZBox(("someaddress", 18000))
        with api_scenario(system, "izbox_detect_active_node"):
            with self.assertRaises(APICommandFailed):
                system.api.get("system")


class ActiveNodeDetectionTest(TestCase):

    def setUp(self):
        super(ActiveNodeDetectionTest, self).setUp()
        self.system = IZBox([("someaddress", 18000), ("someaddress", 28000)])
        self.scenario = api_scenario(self.system, "izbox_detect_active_node")
        self.scenario.start()
        self.addCleanup(self.scenario.end)

    def test_detect_active_node(self):
        api_result = self.system.api.get("system")
        self.assertEquals(api_result.url.hostname, "someaddress")
        self.assertEquals(api_result.url.port, 28000)
