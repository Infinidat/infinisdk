import pytest
from infinisdk.core import Field, SystemObject, TypeBinder


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


def test_get_mutable_fields(binder):
    assert binder.get_mutable_fields() == ['x', 'y']


def test_cache(type_binder):
    with type_binder.fetch_once_context():
        with type_binder.system.api.disable_api_context():
            q = type_binder.get_all()
            assert q is type_binder.get_all()
    assert q is not type_binder.get_all()


def test_nested_cache(type_binder):
    with type_binder.fetch_once_context():
        with type_binder.system.api.disable_api_context():
            with type_binder.fetch_once_context():
                pass


def test_object_caching(volume):
    volume.system.disable_caching()
    assert not volume.get_binder().is_caching_enabled()
    with volume.get_binder().fetch_once_context():
        assert not volume.system.is_caching_enabled()
        assert volume.get_binder().is_caching_enabled()
        with volume.system.api.disable_api_context():
            volume.get_name()
    assert not volume.get_binder().is_caching_enabled()


def test_cached_get_by_id_lazy(volume):
    assert volume.get_binder().get_by_id_lazy(volume.id) is not volume.get_binder().get_by_id_lazy(volume.id)
    with volume.get_binder().fetch_once_context():
        assert volume.get_binder().get_by_id_lazy(volume.id) is volume.get_binder().get_by_id_lazy(volume.id)
        volume2 = volume.get_binder().create(pool=volume.get_pool())
        assert volume.get_binder().get_by_id_lazy(volume2.id) is not volume2
        assert volume.get_binder().get_by_id_lazy(volume2.id) == volume2
