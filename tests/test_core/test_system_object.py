import copy
import gossip
import re
import pytest
from unittest.mock import patch
from infinisdk.core import Field, SystemObject
from infinisdk.core.exceptions import (APICommandFailed,
                                       AttributeAlreadyExists, CacheMiss,
                                       MissingFields, MethodDisabled, InfiniSDKException)
from infinisdk.infinibox.system_object import InfiniBoxSubObject, BaseSystemSubObject
from infinisdk.core.type_binder import SubObjectTypeBinder
from infinisdk.infinibox.share import Share


# pylint: disable=misplaced-comparison-constant, unused-argument


class FakeSystemObject(SystemObject):

    def _is_caching_enabled(self):
        return False


class FakeInfiniBoxSubObject(InfiniBoxSubObject):

    def _is_caching_enabled(self):
        return False


class FakeBaseSystemSubObject(BaseSystemSubObject):

    def _is_caching_enabled(self):
        return False


class BadInfiniBoxSubObject(FakeInfiniBoxSubObject):
    URL_PATH = "bad"

    FIELDS = [
        Field("id", type=int),
        Field(name="name"),
        Field("parent1",
              is_parent_field=True,
              type="infinisdk.infinibox.share:Share",
              ),
        Field("parent2", is_parent_field=True),
    ]


class BadBaseSystemSubObject(FakeBaseSystemSubObject):
    URL_PATH = "bad-base-object"

    FIELDS = [
        Field("id", type=int),
        Field(name="name"),
        Field("parent1", is_parent_field=True),
        Field("parent2", is_parent_field=True),
    ]


class SampleBaseObject(FakeSystemObject):

    FIELDS = [
        Field("id", type=int),
        Field(name="name"),
    ]

class SampleBaseObjectCachingEnabled(FakeSystemObject):

    def _is_caching_enabled(self):
        return True

    FIELDS = [
        Field("id", type=int),
        Field(name="name"),
        Field(name="not_cached_by_default", cached=False),
    ]

class SampleDerivedObject(SampleBaseObject):

    FIELDS = [
        Field(name="number", type=int, creation_parameter=True),
        Field(name="cached_by_default", cached=True),
    ]

    @staticmethod
    def get_type_name():
        return 'infinibox'


class SampleObjectWithStringID(FakeSystemObject):

    FIELDS = [
        Field(name='id', type=str),
    ]


class FakeSystem:

    def is_caching_enabled(self):
        return False

    def is_field_supported(self, field):  # pylint: disable=unused-argument
        return True

    @staticmethod
    def get_type_name():
        return 'infinibox'


def test_cant_have_more_than_one_parent_fields_infinibox_object(system):
    with patch("infinisdk.infinibox.system_object.InfiniBoxSubObject._trigger_pre_create") as mock_gossip:
        mock_gossip.side_effect = gossip.get_hook("infinidat.sdk.pre_creation_data_validation").unregister_all()
        with pytest.raises(InfiniSDKException, match=re.escape("There can only be 1 parent field. Found 2")):
            BadInfiniBoxSubObject.create(system, binder=SubObjectTypeBinder(system, BadInfiniBoxSubObject, Share))

def test_cant_have_more_than_one_parent_fields_base_system_object(system):
    with pytest.raises(InfiniSDKException, match=re.escape("There can only be 1 parent field. Found 2")):
        BadBaseSystemSubObject(system, {"fake_data": "data", "id": 12})


def test_num_fields(system):
    # pylint: disable=no-member
    assert len(SampleBaseObject.fields) == 2
    assert len(SampleDerivedObject.fields) == 4


def test_querying_fields_by_name(system):
    # pylint: disable=no-member
    assert SampleBaseObject.fields.name.type.type is str
    assert SampleDerivedObject.fields.name.type.type is str
    assert SampleDerivedObject.fields.number.type.type is int


def test_no_fields(system):
    class EmptyObject(FakeSystemObject):
        pass

    assert len(EmptyObject.fields) == 0  # pylint: disable=no-member


def test_nonexistent_field(system):
    assert not hasattr(SampleDerivedObject.fields, "fake_field")  # pylint: disable=no-member


def test_get_from_cache_miss(system):
    obj = SampleDerivedObject(system, {"id": 1})
    assert obj.id == 1
    with pytest.raises(CacheMiss):
        obj.get_field("number", from_cache=True, fetch_if_not_cached=False)

def test_get_from_cache_context(system):
    not_cached_field_name, not_cached_field_value = "not_cached_by_default", "bla"
    obj = SampleBaseObjectCachingEnabled(system, {"id": 1, not_cached_field_name: not_cached_field_value})
    obj.invalidate_cache(not_cached_field_name)
    with obj.using_cache_by_default():
        with pytest.raises(CacheMiss):
            obj.get_field(not_cached_field_name, fetch_if_not_cached=False)
    with pytest.raises(APICommandFailed): #validate not going to cache
        obj.get_field(not_cached_field_name, fetch_if_not_cached=False)

def test_get_from_cache_hit(system):
    obj = SampleDerivedObject(FakeSystem(), {"id": 1, "number": 2})
    assert obj.id == 1
    assert 2 == obj.get_field('number', from_cache=True)


def test_get_from_cache_by_default(system):
    value = "some_value_here"
    obj = SampleDerivedObject(
        FakeSystem(), {"id": 1, "cached_by_default": value})
    assert obj.get_field('cached_by_default') == value


def _attach_method(instance, function):
    import types
    setattr(instance, function.__name__, types.MethodType(function, instance))


@pytest.mark.parametrize("with_fields", [True, False])
def test_requires_cache_invalidation_decorator(system, with_fields):
    obj = SampleDerivedObject(system, {"id": 1, "number": 2, "string": "asdf"})

    @SystemObject.requires_cache_invalidation("number", "string")
    def get_meaning_of_life(self, *args, **kwargs): # pylint: disable=unused-argument
        return 42
    if with_fields:
        get_meaning_of_life = SystemObject.requires_cache_invalidation(
            "number", "string")(get_meaning_of_life)
    else:
        get_meaning_of_life = SystemObject.requires_cache_invalidation(
            get_meaning_of_life)
    _attach_method(obj, get_meaning_of_life)
    assert 1 == obj.get_field('id', from_cache=True, fetch_if_not_cached=False)
    assert 2 == obj.get_field(
        'number', from_cache=True, fetch_if_not_cached=False)
    assert "asdf" == obj.get_field(
        'string', from_cache=True, fetch_if_not_cached=False)
    assert 42 == obj.get_meaning_of_life("Douglas", last_name="Adams")
    if with_fields:
        assert 1 == obj.get_field(
            'id', from_cache=True, fetch_if_not_cached=False)
    else:
        with pytest.raises(CacheMiss):
            obj.get_field("id", from_cache=True, fetch_if_not_cached=False)
    with pytest.raises(CacheMiss):
        obj.get_field("number", from_cache=True, fetch_if_not_cached=False)
    with pytest.raises(CacheMiss):
        obj.get_field("string", from_cache=True, fetch_if_not_cached=False)


def test_auto_getter_attribute_already_exists_in_same_class(system):
    with pytest.raises(AttributeAlreadyExists):
        class SomeObjectForGetter(FakeSystemObject):  # pylint: disable=unused-variable
            FIELDS = [Field("id", type=int)]
            get_id = lambda self: 'my id'

    with pytest.raises(AttributeAlreadyExists):
        class SomeObjectForUpdater(FakeSystemObject):  # pylint: disable=unused-variable
            FIELDS = [Field("id", type=int, mutable=True)]
            _id = 'my id'

            def update_id(self, value): self._id = value  # pylint: disable=multiple-statements


def test_auto_getter_attribute_already_exists_in_base_class1(system):
    class SomeObject(FakeSystemObject):
        FIELDS = [Field("id", type=int)]

    class SomeDerivedObject(SomeObject):
        _id = 'other id'

        def get_id(self): return self._id  # pylint: disable=multiple-statements

        def update_id(self, value): self._id = value  # pylint: disable=multiple-statements

    some_derived_obj = SomeDerivedObject(FakeSystem(), {"id": 1})
    assert some_derived_obj.get_id() == 'other id'
    some_derived_obj.update_id('bla bla')
    assert some_derived_obj.get_id() == 'bla bla'


def test_auto_getter_attribute_already_exists_in_base_class2(system):
    class SomeObject(FakeSystemObject):
        _id = 'my id'

        def get_id(self): return self._id  # pylint: disable=multiple-statements

        def update_id(self, value): self._id = value  # pylint: disable=multiple-statements

    class SomeDerivedObject(SomeObject):
        FIELDS = [Field("id", type=int, cached=True, mutable=True)]

    some_derived_obj = SomeDerivedObject(FakeSystem(), {"id": 1})
    assert some_derived_obj.get_id() == 1


def test__equality(system):
    system1 = object()
    system2 = object()
    Obj = SampleDerivedObject
    equal1, equal2 = [
        Obj(system1, {"id": 100})
        for _ in range(2)
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


def test_get_fields_without_field_names(infinibox):
    user = infinibox.users.choose()
    fields = user.get_fields()
    # "username" is the API name for "name" field
    assert "name" in fields
    assert "username" not in fields


def test_is_in_system_with_get_from_cache_context(infinibox, volume):
    assert volume.is_in_system()
    with volume.using_cache_by_default():
        assert volume.is_in_system()
        with infinibox.api.disable_api_context():
            with pytest.raises(MethodDisabled):
                volume.is_in_system()


def test_object_creation_missing_fields():
    with pytest.raises(MissingFields):
        SampleDerivedObject.create(FakeSystem())


def test_get_url_path(system, user):
    assert system.users.get_url_path() == user.get_url_path(system)


def test_update_field_updates_its_cache(user):
    new_name = "testing_update_field_caching"
    assert user.get_name(from_cache=True) != new_name
    user.update_name(new_name)
    assert user.get_name(from_cache=True) == new_name


def test_update_field_does_not_update_other_fields_cache(user):
    some_email = 'some@email.com'
    user.update_field_cache({'email': some_email})
    user.update_name('some_new_name')
    assert user.get_email(from_cache=True) == some_email


def test_string_id_escaping(system):
    """Make sure that objects with string-based ids properly encode their url path
    """
    obj = SampleObjectWithStringID(system, {'id': 'some:text'})
    with pytest.raises(APICommandFailed) as caught:
        field = obj.get_field('x')  # pylint: disable=unused-variable

    url = caught.value.response.response.request.url
    assert url.endswith(
        '/api/rest/sampleobjectwithstringids/some%3Atext?fields=x')


def test_deepcopy(system_object):
    new_system_object = copy.deepcopy(system_object)
    assert new_system_object is not system_object
    assert new_system_object.system is system_object.system
    assert new_system_object._cache is not system_object._cache # pylint: disable=protected-access


@pytest.fixture(params=[SampleBaseObject, SampleDerivedObject])
def system_object(request, system):
    return request.param(system, {'id': 1})
