from sentinels import NOTHING


def test_invalidate_cache(infinibox, component):
    fake_field_name = 'foo'
    fake_field_value = 'bar'
    component_uid = component.id
    assert infinibox.components.get(uid=component_uid) is component
    component.update_field_cache({fake_field_name: fake_field_value})
    assert component._cache.get(fake_field_name) == fake_field_value  # pylint: disable=protected-access
    infinibox.components.invalidate_cache()
    assert component._cache.get('parent_id') is not None  # pylint: disable=protected-access
    if component != infinibox.components.system_component:
        assert component.get_parent().id
    else:
        assert component.get_parent() is None
    infinibox.components.get_rack_1().refresh_cache()
    assert infinibox.components.try_get_component_by_id(component_uid) is component
    curr_component = infinibox.components.get(uid=component_uid)
    assert curr_component._cache.get(fake_field_name, NOTHING) is NOTHING  # pylint: disable=protected-access
    assert curr_component is component


def test_listing_nodes_after_invalidate_cache(infinibox):
    infinibox.components.invalidate_cache()
    infinibox.compat.invalidate_cache()
    infinibox.components.nodes.to_list()
