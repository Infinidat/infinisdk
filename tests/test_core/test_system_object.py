from ..utils import TestCase
from infinipy2.core import *

class SampleBaseObject(SystemObject):
    FIELDS = [
        Field(name="name"),
    ]

class SampleDerivedObject(SampleBaseObject):
    FIELDS = [
        Field(name="number", type=int),
    ]

class SystemObjectTest(TestCase):

    def test_num_fields(self):
        self.assertEquals(len(SampleBaseObject.fields), 1)
        self.assertEquals(len(SampleDerivedObject.fields), 2)

    def test_querying_fields_by_name(self):
        self.assertIs(SampleBaseObject.fields.name.type.type, str)
        self.assertIs(SampleDerivedObject.fields.name.type.type, str)
        self.assertIs(SampleDerivedObject.fields.number.type.type, int)

    def test_no_fields(self):
        class EmptyObject(SystemObject):
            pass

        self.assertEquals(len(EmptyObject.fields), 0)


