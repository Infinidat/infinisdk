import pytest
from infinisdk.core import SystemObject, TypeBinder


def test_unknown_attributes_raise_attribute_error(system):
    objects = system.objects
    with pytest.raises(AttributeError):
        objects.nonexisting  # pylint: disable=pointless-statement

def test_get_types(system):
    all_types = system.objects.get_types()
    assert [] != all_types
    exclude_type_names = ['nlm_lock']
    system_object_types = set(all_types) - set([x for x in all_types if x.get_type_name() in exclude_type_names])
    assert all(issubclass(x, SystemObject) for x in system_object_types)


def test_get_all_collections(system):
    assert [] != system.get_collections()
    assert all(isinstance(collection, TypeBinder) for collection in system.get_collections())
    assert list(system.objects) == system.get_collections()
    assert len(system.get_collections_names()) == len(system.objects) == len(system.get_collections())
