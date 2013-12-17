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
        Field(name="cached_by_default", cached=True),
    ]

class SystemObjectFieldsTest(TestCase):

    def setUp(self):
        super(SystemObjectFieldsTest, self).setUp()
        self.system = object()

    def test_num_fields(self):
        self.assertEquals(len(SampleBaseObject.fields), 2)
        self.assertEquals(len(SampleDerivedObject.fields), 4)

    def test_querying_fields_by_name(self):
        self.assertIs(SampleBaseObject.fields.name.type.type, str)
        self.assertIs(SampleDerivedObject.fields.name.type.type, str)
        self.assertIs(SampleDerivedObject.fields.number.type.type, int)

    def test_no_fields(self):
        class EmptyObject(SystemObject):
            pass

        self.assertEquals(len(EmptyObject.fields), 0)

    def test_get_from_cache_miss(self):
        obj = SampleDerivedObject(self.system, {"id": 1})
        self.assertEquals(obj.id, 1)
        with self.assertRaises(CacheMiss):
            obj.get_field("number", from_cache=True, fetch_if_not_cached=False)

    def test_get_from_cache_hit(self):
        obj = SampleDerivedObject(self.system, {"id": 1, "number": 2})
        self.assertEquals(obj.id, 1)
        self.assertEquals(2, obj.get_field("number", from_cache=True))

    def test_get_from_cache_by_default(self):
        value = "some_value_here"
        obj = SampleDerivedObject(self.system, {"id": 1, "cached_by_default": value})
        self.assertEquals(obj.get_field("cached_by_default"), value)


class SystemObjectEqualityTest(TestCase):

    def test__equality(self):
        system1 = object()
        system2 = object()
        Obj = SampleDerivedObject
        equal1, equal2 = [
            Obj(system1, {"id": 100})
            for i in range(2)
        ]
        self.assertTrue(equal1 == equal2)
        self.assertFalse(equal1 != equal2)
        self.assertEquals(hash(equal1), hash(equal2))

        for unequal1, unequal2 in [
                (Obj(system1, {"id": 100}), Obj(system2, {"id": 100})),
                (Obj(system1, {"id": 100}), Obj(system1, {"id": 101})),
                ]:
            self.assertTrue(unequal1 != unequal2)
            self.assertFalse(unequal1 == unequal2)
            self.assertNotEquals(hash(unequal1), hash(unequal2))

        diff_type2 = SampleBaseObject(system1, {"id": 100})
        diff_type1 = SampleDerivedObject(system1, {"id": 100})
        self.assertEqual(NotImplemented, diff_type1.__eq__(diff_type2))

class SystemObjectCreationTest(TestCase):

    def test_object_creation_missing_fields(self):
        dummy_system = object()
        with self.assertRaises(MissingFields):
            SampleDerivedObject.create(dummy_system)

