import pytest
from sentinels import NOTHING


@pytest.mark.only_latest
def test_invalidate_cache(infinibox, component):
    fake_field_name = 'foo'
    fake_field_value = 'bar'
    component_uid = component.id
    assert infinibox.components.get(uid=component_uid) is component
    component.update_field_cache({fake_field_name: fake_field_value})
    assert component._cache.get(fake_field_name) == fake_field_value  # pylint: disable=protected-access
    infinibox.components.invalidate_cache()
    parent_id = component._cache.get('parent_id', NOTHING)  # pylint: disable=protected-access
    assert parent_id is not NOTHING
    if component is infinibox.components.system_component or isinstance(component, (
            infinibox.components.service_clusters.object_type,
            infinibox.components.external_clusters.object_type)):
        assert not parent_id
        assert component.get_parent() is None
    else:
        assert isinstance(parent_id, (str, bytes))
        assert component.get_parent().id
    infinibox.components.get_rack_1().refresh_cache()
    assert infinibox.components.try_get_component_by_id(component_uid) is component
    curr_component = infinibox.components.get(uid=component_uid)
    assert curr_component._cache.get(fake_field_name, NOTHING) is NOTHING  # pylint: disable=protected-access
    assert curr_component is component


def test_listing_nodes_after_invalidate_cache(infinibox):
    infinibox.components.invalidate_cache()
    infinibox.compat.invalidate_cache()
    infinibox.components.nodes.to_list()


@pytest.mark.only_latest
def test_getting_component_fields_after_cache_invalidation(infinibox, component):
    assert component.fields.index.is_identity  # ComputedIDBinding assumes that index field is identity one
    infinibox.components.invalidate_cache()
    infinibox.compat.invalidate_cache()
    for field in component.fields:
        if not field.add_getter:
            continue
        if not infinibox.is_field_supported(field):
            continue
        getter = getattr(component, field.getter_name)
        getter()
    component.get_collection().to_list()
