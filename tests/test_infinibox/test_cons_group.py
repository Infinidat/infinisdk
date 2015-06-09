import pytest
from ..conftest import new_to_version
from infinisdk.infinibox.cons_group import ConsGroup
from api_object_schema.utils import loose_isinstance


@new_to_version('2.2')
def test_create_cg(infinibox, pool):
    cg = infinibox.cons_groups.create(pool=pool)
    assert cg.is_in_system()


@new_to_version('2.2')
@pytest.mark.parametrize('field', ConsGroup.FIELDS)
def test_get_cg_fields(cg, field):
    field_value = cg.get_field(field.name)
    if field.name == 'parent':
        assert field_value is None
    else:
        assert loose_isinstance(field_value, field.type.type)


@new_to_version('2.2')
def test_get_members(cg, volume, filesystem):
    assert len(cg.get_members()) == 0
    assert cg.get_members_count() == 0
    cg.add_member(volume)
    cg.add_member(filesystem)
    members = cg.get_members()
    assert len(members) == 2
    assert filesystem in members
    assert volume in members
    assert cg.get_members_count() == 2
    cg.remove_member(volume)
    assert len(cg.get_members()) == 1
    cg.remove_member(filesystem)
    assert cg.get_members_count() == 0
    assert len(cg.get_members()) == 0


@pytest.fixture
def cg(request, pool):
    return pool.system.cons_groups.create(pool=pool)
