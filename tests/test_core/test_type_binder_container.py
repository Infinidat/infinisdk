import pytest
from infinisdk.core import *


def test_unknown_attributes_raise_attribute_error(system):
    objects = system.objects
    with pytest.raises(AttributeError):
        objects.nonexisting

def test_get_types(system):
    assert [] != system.objects.get_types()
    assert all(issubclass(x, SystemObject) for x in system.objects.get_types())

