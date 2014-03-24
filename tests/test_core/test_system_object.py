from ..utils import CoreTestCase
from infinipy2.core import Field, SystemObject
from infinipy2.core.exceptions import (MissingFields, CacheMiss,
                                       AttributeAlreadyExists)

class SampleBaseObject(SystemObject):
    FIELDS = [
        Field("id"),
        Field(name="name"),
    ]

class SampleDerivedObject(SampleBaseObject):
    FIELDS = [
        Field(name="number", type=int, creation_parameter=True),
        Field(name="cached_by_default", cached=True),
    ]

class SystemObjectFieldsTest(CoreTestCase):

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

    def test_unexist_field(self):
        self.assertRaises(AttributeError, getattr, SampleDerivedObject.fields, 'fake_field')

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

    def test_auto_getter_attribute_already_exists_in_same_class(self):
        with self.assertRaises(AttributeAlreadyExists):
            class SomeObjectForGetter(SystemObject):
                FIELDS = [Field("id")]
                get_id = lambda self: 'my id'

        with self.assertRaises(AttributeAlreadyExists):
            class SomeObjectForUpdater(SystemObject):
                FIELDS = [Field("id", mutable=True)]
                _id = 'my id'
                def update_id(self, value): self._id = value

    def test_auto_getter_attribute_already_exists_in_base_class1(self):
        class SomeObject(SystemObject):
            FIELDS = [Field("id")]

        class SomeDerivedObject(SomeObject):
            _id = 'other id'
            def get_id(self): return self._id
            def update_id(self, value): self._id = value

        some_derived_obj = SomeDerivedObject(self.system, {"id": 1})
        self.assertEquals(some_derived_obj.get_id(), 'other id')
        some_derived_obj.update_id('bla bla')
        self.assertEquals(some_derived_obj.get_id(), 'bla bla')

    def test_auto_getter_attribute_already_exists_in_base_class2(self):
        class SomeObject(SystemObject):
            _id = 'my id'
            def get_id(self): return self._id
            def update_id(self, value): self._id = value

        class SomeDerivedObject(SomeObject):
            FIELDS = [Field("id", cached=True, mutable=True)]

        some_derived_obj = SomeDerivedObject(self.system, {"id": 1})
        self.assertEquals(some_derived_obj.get_id(), 1)


class SystemObjectEqualityTest(CoreTestCase):

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

class SystemObjectCreationTest(CoreTestCase):

    def test_object_creation_missing_fields(self):
        dummy_system = object()
        with self.assertRaises(MissingFields):
            SampleDerivedObject.create(dummy_system)

