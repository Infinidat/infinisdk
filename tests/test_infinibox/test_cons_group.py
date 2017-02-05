import pytest
from ..conftest import relevant_from_version
from infinisdk.infinibox.cons_group import ConsGroup
from api_object_schema.utils import loose_isinstance


@relevant_from_version('2.2')
def test_create_cg(infinibox, pool):
    cg = infinibox.cons_groups.create(pool=pool)
    assert cg.is_in_system()
    assert cg.is_master()
    assert not cg.is_snapgroup()


@relevant_from_version('2.2')
@pytest.mark.parametrize('field', ConsGroup.FIELDS)
def test_get_cg_fields(cg, field):
    field_value = cg.get_field(field.name)
    if field.name in {'parent', 'rmr_snapshot_guid', 'data_snapshot_guid'}:
        assert field_value is None
    else:
        assert loose_isinstance(field_value, field.type.type)


@relevant_from_version('2.2')
def test_get_members(cg, volume):
    assert len(cg.get_members()) == 0
    assert cg.get_members_count() == 0
    cg.add_member(volume)
    members = cg.get_members()
    assert len(members) == 1
    assert volume in members
    assert cg.get_members_count() == 1
    cg.remove_member(volume)
    assert cg.get_members_count() == 0
    assert len(cg.get_members()) == 0


@relevant_from_version('2.2')
def test_get_rmr_snapshot_guid(cg):
    assert cg.get_rmr_snapshot_guid() is None



@pytest.fixture
def cg(pool):
    return pool.system.cons_groups.create(pool=pool)
