from infinipy2.core import *
from ..utils import TestCase

class TypeBinderContainerTest(TestCase):

    API_SCENARIOS = ["izbox_queries"]

    def test_unknown_attributes_raise_attribute_error(self):
        objects = self.system.objects
        with self.assertRaises(AttributeError):
            objects.nonexisting

