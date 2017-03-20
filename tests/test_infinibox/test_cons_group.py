import gossip
import pytest
from api_object_schema.utils import loose_isinstance
from infinisdk.core.exceptions import APICommandFailed
from infinisdk.infinibox.cons_group import ConsGroup
from munch import Munch

from ..conftest import relevant_from_version


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
    hook_ident = 'unittest_ident'

    assert len(cg.get_members()) == 0
    assert cg.get_members_count() == 0
    add_hook_status = Munch(pre_called=False, post_called=False, failure_called=False)
    remove_hook_status = Munch(pre_called=False, post_called=False, failure_called=False)

    @gossip.register('infinidat.sdk.pre_cons_group_add_member', token=hook_ident)
    def pre_add_member(cons_group, member, request): # pylint: disable=unused-variable,unused-argument
        assert member is volume
        assert cons_group is cg
        add_hook_status.pre_called = True

    @gossip.register('infinidat.sdk.post_cons_group_add_member', token=hook_ident)
    def post_add_member(cons_group, member, request): # pylint: disable=unused-variable,unused-argument
        assert member is volume
        assert cons_group is cg
        add_hook_status.post_called = True

    @gossip.register('infinidat.sdk.cons_group_add_member_failure', token=hook_ident)
    def add_member_failure(cons_group, member, request): # pylint: disable=unused-variable,unused-argument
        assert member is volume
        assert cons_group is cg
        add_hook_status.failure_called = True

    cg.add_member(volume)

    assert add_hook_status.pre_called
    assert add_hook_status.post_called
    assert not add_hook_status.failure_called

    add_hook_status.pre_called = add_hook_status.post_called = add_hook_status.failure_called = False

    members = cg.get_members()
    assert len(members) == 1
    assert volume in members
    assert cg.get_members_count() == 1

    @gossip.register('infinidat.sdk.pre_cons_group_remove_member', token=hook_ident)
    def pre_remove_member(cons_group, member): # pylint: disable=unused-variable
        assert member is volume
        assert cons_group is cg
        remove_hook_status.pre_called = True

    @gossip.register('infinidat.sdk.post_cons_group_remove_member', token=hook_ident)
    def post_remove_member(cons_group, member): # pylint: disable=unused-variable
        assert member is volume
        assert cons_group is cg
        remove_hook_status.post_called = True

    @gossip.register('infinidat.sdk.cons_group_remove_member_failure', token=hook_ident)
    def remove_member_failure(cons_group, member): # pylint: disable=unused-variable
        assert member is volume
        assert cons_group is cg
        remove_hook_status.failure_called = True

    cg.remove_member(volume)

    assert remove_hook_status.pre_called
    assert remove_hook_status.post_called
    assert not remove_hook_status.failure_called

    remove_hook_status.pre_called = remove_hook_status.post_called = remove_hook_status.failure_called = False

    with pytest.raises(APICommandFailed):
        cg.remove_member(volume)

    assert remove_hook_status.pre_called
    assert not remove_hook_status.post_called
    assert remove_hook_status.failure_called

    volume.delete()
    with pytest.raises(APICommandFailed):
        cg.add_member(volume)

    assert add_hook_status.pre_called
    assert not add_hook_status.post_called
    assert add_hook_status.failure_called

    assert cg.get_members_count() == 0
    assert len(cg.get_members()) == 0

    gossip.unregister_token(hook_ident)


@relevant_from_version('2.2')
def test_get_rmr_snapshot_guid(cg):
    assert cg.get_rmr_snapshot_guid() is None



@pytest.fixture
def cg(pool):
    return pool.system.cons_groups.create(pool=pool)
