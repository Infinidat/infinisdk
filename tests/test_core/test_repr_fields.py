import itertools

import pytest
from infinisdk.core import Field, SystemObject


def test_default_repr_identical_to_str(system_obj):
    assert repr(system_obj) == str(system_obj)


def test_default_repr_identical_to_str_repr_Field(name_repr_obj):
    assert repr(name_repr_obj) == str(name_repr_obj)


def test_object_id_in_default_repr(system_obj, object_id):
    assert str(object_id) in repr(system_obj)


def test_repr_field_in_repr(system, name_repr_obj):
    assert 'name' in repr(name_repr_obj)


def test_uncached_fields_in_repr(system, name_repr_obj):
    assert 'name=?' in repr(name_repr_obj)


@pytest.fixture
def system_obj(system, object_id):
    return _create_object(system, object_id)


@pytest.fixture
def system(is_caching_enabled):
    class _System(object):
        pass

    return _System()


@pytest.fixture(params=[True, False])
def is_caching_enabled(request):
    return request.param

@pytest.fixture
def name_repr_obj(system, object_id):
    returned = _create_object(
        system, object_id, extra_fields=[Field('name', use_in_repr=True)])
    assert 'name' not in returned._cache
    return returned


@pytest.fixture
def object_id():
    return next(_object_ids)

_object_ids = itertools.count(1000)


def _create_object(system, object_id, extra_fields=()):
    class _Object(SystemObject):
        FIELDS = [
            Field("id", type=int, ),
        ] + list(extra_fields)

    return _Object(system, {'id': object_id})
