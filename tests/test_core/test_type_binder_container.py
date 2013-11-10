from infinipy2.core import *
from ..utils import TestCase

class TypeBinderContainerTest(TestCase):


    def test_unknown_attributes_raise_attribute_error(self):
        objects = self.system.objects
        with self.assertRaises(AttributeError):
            objects.nonexisting

    def test_get_types(self):
        self.assertNotEquals([], self.system.objects.get_types())
        self.assertTrue(
            all(issubclass(x, SystemObject) for x in self.system.objects.get_types()))

