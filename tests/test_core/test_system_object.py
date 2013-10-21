from ..utils import TestCase
from infinipy2.core import *
from infinipy2.core.exceptions import MissingFields, CacheMiss

class SampleBaseObject(SystemObject):
    FIELDS = [
        Field("id"),
        Field(name="name"),
    ]

class SampleDerivedObject(SampleBaseObject):
    FIELDS = [
        Field(name="number", type=int, mandatory=True),
    ]

class SystemObjectFieldsTest(TestCase):

    def test_num_fields(self):
        self.assertEquals(len(SampleBaseObject.fields), 2)
        self.assertEquals(len(SampleDerivedObject.fields), 3)

    def test_querying_fields_by_name(self):
        self.assertIs(SampleBaseObject.fields.name.type.type, str)
        self.assertIs(SampleDerivedObject.fields.name.type.type, str)
        self.assertIs(SampleDerivedObject.fields.number.type.type, int)

    def test_no_fields(self):
        class EmptyObject(SystemObject):
            pass

        self.assertEquals(len(EmptyObject.fields), 0)

    def test_get_from_cache_miss(self):
        obj = SampleDerivedObject(object(), {"id": 1})
        self.assertEquals(obj.id, 1)
        with self.assertRaises(CacheMiss):
            obj.get_field("number", from_cache=True)

    def test_get_from_cache_hit(self):
        obj = SampleDerivedObject(object(), {"id": 1, "number": 2})
        self.assertEquals(obj.id, 1)
        self.assertEquals(2, obj.get_field("number", from_cache=True))


class SystemObjectCreationTest(TestCase):

    def test_object_creation_missing_fields(self):
        dummy_system = object()
        with self.assertRaises(MissingFields):
            SampleDerivedObject.create(dummy_system)

