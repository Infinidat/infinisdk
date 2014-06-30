import pytest
from infinipy2.core import Field, SystemObject
from infinipy2.core.exceptions import (AttributeAlreadyExists, CacheMiss,
                                       MissingFields)


class SampleBaseObject(SystemObject):
    FIELDS = [
        Field("id", type=int),
        Field(name="name"),
    ]

class SampleDerivedObject(SampleBaseObject):
    FIELDS = [
        Field(name="number", type=int, creation_parameter=True),
        Field(name="cached_by_default", cached=True),
    ]


_fake_system = object()

def test_num_fields(system):
    assert len(SampleBaseObject.fields) == 2
    assert len(SampleDerivedObject.fields) == 4

def test_querying_fields_by_name(system):
    assert SampleBaseObject.fields.name.type.type is str
    assert SampleDerivedObject.fields.name.type.type is str
    assert SampleDerivedObject.fields.number.type.type is int

def test_no_fields(system):
    class EmptyObject(SystemObject):
        pass

    assert len(EmptyObject.fields) == 0

def test_unexist_field(system):
    assert not hasattr(SampleDerivedObject.fields, "fake_field")

def test_get_from_cache_miss(system):
    obj = SampleDerivedObject(system, {"id": 1})
    assert obj.id == 1
    with pytest.raises(CacheMiss):
        obj.get_field("number", from_cache=True, fetch_if_not_cached=False)

def test_get_from_cache_hit(system):
    obj = SampleDerivedObject(_fake_system, {"id": 1, "number": 2})
    assert obj.id == 1
    assert 2 == obj.get_field('number', from_cache=True)

def test_get_from_cache_by_default(system):
    value = "some_value_here"
    obj = SampleDerivedObject(_fake_system, {"id": 1, "cached_by_default": value})
    assert obj.get_field('cached_by_default') == value

def test_auto_getter_attribute_already_exists_in_same_class(system):
    with pytest.raises(AttributeAlreadyExists):
        class SomeObjectForGetter(SystemObject):
            FIELDS = [Field("id", type=int)]
            get_id = lambda self: 'my id'

    with pytest.raises(AttributeAlreadyExists):
        class SomeObjectForUpdater(SystemObject):
            FIELDS = [Field("id", type=int, mutable=True)]
            _id = 'my id'
            def update_id(self, value): self._id = value

def test_auto_getter_attribute_already_exists_in_base_class1(system):
    class SomeObject(SystemObject):
        FIELDS = [Field("id", type=int)]

    class SomeDerivedObject(SomeObject):
        _id = 'other id'
        def get_id(self): return self._id
        def update_id(self, value): self._id = value

    some_derived_obj = SomeDerivedObject(_fake_system, {"id": 1})
    assert some_derived_obj.get_id() == 'other id'
    some_derived_obj.update_id('bla bla')
    assert some_derived_obj.get_id() == 'bla bla'

def test_auto_getter_attribute_already_exists_in_base_class2(system):
    class SomeObject(SystemObject):
        _id = 'my id'
        def get_id(self): return self._id
        def update_id(self, value): self._id = value

    class SomeDerivedObject(SomeObject):
        FIELDS = [Field("id", type=int, cached=True, mutable=True)]

    some_derived_obj = SomeDerivedObject(_fake_system, {"id": 1})
    assert some_derived_obj.get_id() == 1


def test__equality(system):
    system1 = object()
    system2 = object()
    Obj = SampleDerivedObject
    equal1, equal2 = [
        Obj(system1, {"id": 100})
        for i in range(2)
    ]
    assert equal1 == equal2
    assert (not equal1 != equal2)
    assert hash(equal1) == hash(equal2)

    for unequal1, unequal2 in [
            (Obj(system1, {"id": 100}), Obj(system2, {"id": 100})),
            (Obj(system1, {"id": 100}), Obj(system1, {"id": 101})),
            ]:
        assert unequal1 != unequal2
        assert not (unequal1 == unequal2)
        assert hash(unequal1) != hash(unequal2)

    diff_type2 = SampleBaseObject(system1, {"id": 100})
    diff_type1 = SampleDerivedObject(system1, {"id": 100})
    assert NotImplemented == diff_type1.__eq__(diff_type2)

def test_get_fields_without_field_names(system):
    user = system.users.choose()
    fields = user.get_fields()
    # For both infinibox & izbox, "username" is the API name for "name" field
    assert "name" in fields
    assert "username" not in fields

def test_object_creation_missing_fields():
    with pytest.raises(MissingFields):
        SampleDerivedObject.create(_fake_system)

def test_update_field_updates_its_cache(system):
    new_name = "testing_update_field_caching"
    user = system.users.create()
    assert user.get_field("name", from_cache=True) != new_name
    user.update_name(new_name)
    assert user.get_field("name", from_cache=True) == new_name
