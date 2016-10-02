import pytest
from infinisdk.core import SystemObject, TypeBinder


def test_unknown_attributes_raise_attribute_error(system):
    objects = system.objects
    with pytest.raises(AttributeError):
        objects.nonexisting  # pylint: disable=pointless-statement

def test_get_types(system):
    assert [] != system.objects.get_types()
    assert all(issubclass(x, SystemObject) for x in system.objects.get_types())


def test_get_all_collections(system):
    assert [] != system.get_collections()
    assert all(isinstance(collection, TypeBinder) for collection in system.get_collections())
    assert list(system.objects) == system.get_collections()
    assert len(system.get_collections_names()) == len(system.objects) == len(system.get_collections())
