from infinipy2.core import *
from infinipy2.izbox import IZBox
from infinipy2.izbox.filesystem import Filesystem
from ..utils import TestCase
from ..utils import api_scenario
from urlobject import URLObject

class TypeBinderContainerTest(TestCase):

    def setUp(self):
        super(TypeBinderContainerTest, self).setUp()
        self.system = IZBox(("address", 80))
        self.scenario = api_scenario(self.system, "izbox_handshake")
        self.scenario.start()
        self.addCleanup(self.scenario.end)

    def test_unknown_attributes_raise_attribute_error(self):
        objects = self.system.objects
        with self.assertRaises(AttributeError):
            objects.nonexisting

