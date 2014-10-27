import pytest
from infinisdk.core import Field, SystemObject, TypeBinder


def test_get_mutable_fields(binder):
    assert binder.get_mutable_fields() == ['x', 'y']


class SampleObject(SystemObject):
    FIELDS = [
        Field('id', type=int),
        Field('x', mutable=True),
        Field('y'),
        Field('z', mutable=True),
    ]


@pytest.fixture
def binder(system):
    return TypeBinder(SampleObject, system)
