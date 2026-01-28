import gossip
import pytest
from api_object_schema.utils import loose_isinstance
from infinisdk.core.exceptions import APICommandFailed
from infinisdk.infinibox.cons_group import ConsGroup
from munch import Munch
from ..conftest import create_volume
from infinisdk.core.exceptions import InvalidUsageException

def test_create_cg(infinibox, pool):
    cg = infinibox.cons_groups.create(pool=pool)
    assert cg.is_in_system()
    assert cg.is_master()
    assert not cg.is_snapgroup()


def test_replicate_to_async_target_url_param(cg, volume):
    cg.add_member(volume)
    snap = cg.create_snapshot(replicate_to_async_target=False)
    assert snap.get_parent() == cg

@pytest.mark.parametrize('field', ConsGroup.FIELDS)
def test_get_cg_fields(cg, field):
    if not cg.system.is_field_supported(field):
        return
    field_value = cg.get_field(field.name)
    fields_with_initial_none = {
            'parent',
            'rmr_snapshot_guid',
            'data_snapshot_guid',
            'lock_expires_at',
            'created_by_policy',
            "created_by_snapshot_policy_name",
            'snapshot_retention',
            'snapshot_expires_at',
            "created_by_schedule",
            "created_by_schedule_name",
            "remote_snapshot_retention",
            "remote_snapshot_retention_lock",
            }
    if field.name in fields_with_initial_none:
        assert field_value is None
    else:
        assert loose_isinstance(field_value, field.type.type)


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


def test_get_rmr_snapshot_guid(cg):
    assert cg.get_rmr_snapshot_guid() is None


def test_promote_snapshot(infinibox, pool):
    cg = pool.system.cons_groups.create(pool=pool)
    for _ in range(3):
        volume = create_volume(infinibox, pool_id=pool.id)
        cg.add_member(volume)

    cg_snapshot = cg.create_snapshot()

    cg_snapshot_volume_types = [member.get_type() for member in cg_snapshot.get_members().to_list()]
    assert all(volume_type == 'SNAPSHOT' for volume_type in cg_snapshot_volume_types)
    
    promoted_cg_snapshot = cg_snapshot.promote_snapshot()
    
    assert promoted_cg_snapshot == cg_snapshot
    assert promoted_cg_snapshot.get_type() == "MASTER"

    promoted_cg_snapshot_volume_types = [member.get_type() for member in promoted_cg_snapshot.get_members().to_list()]
    assert all(volume_type == 'MASTER' for volume_type in promoted_cg_snapshot_volume_types)

def test_create_snap_group_with_remote_snapshot_retention_and_remote_snapshot_retention_lock(cg_replica):
    cg_snapshot = cg_replica.get_local_entity().create_snapshot(remote_snapshot_retention=86400, remote_snapshot_retention_lock=86400)

    cg_snapshot_remote_snapshot_retention = cg_snapshot.get_remote_snapshot_retention()
    assert cg_snapshot_remote_snapshot_retention == 86400
    
    cg_snapshot_remote_snapshot_retention_lock = cg_snapshot.get_remote_snapshot_retention_lock()
    assert cg_snapshot_remote_snapshot_retention_lock == 86400

def test_delete_with_invalid_delete_members_value(cg):
    with pytest.raises(InvalidUsageException, match="Invalid value for delete_members"):
        cg.delete(delete_members="Yes")