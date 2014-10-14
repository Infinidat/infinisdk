import time
import arrow
from functools import partial

import flux
from capacity import GB, Capacity

import gossip
import pytest
from infinisdk.core.translators_and_types import MillisecondsDatetimeTranslator
from infinisdk.core.exceptions import (APICommandFailed,
                                       InvalidOperationException)
from infinisdk.infinibox.volume import _BEGIN_FORK_HOOK, _FINISH_FORK_HOOK, Volume
from infinisdk.infinibox.pool import Pool
from infinisdk.infinibox.scsi_serial import SCSISerial

from ..conftest import create_pool, create_volume


def test_unmapping(infinibox, mapped_volume):
    assert mapped_volume.get_logical_units()
    mapped_volume.unmap()
    assert not mapped_volume.get_logical_units()

def test_move_pool(infinibox, volume, pool):
    new_pool = create_pool(infinibox)
    assert volume.get_pool() == pool
    volume.move_pool(new_pool)
    assert volume.get_pool() == new_pool

def test_serial(infinibox, volume):
    assert isinstance(volume.get_serial(), SCSISerial)

def test_allocated(infinibox, volume):
    assert isinstance(volume.get_allocated(), Capacity)

def test_field_types():
    assert Volume.fields.parent.type.type is Volume
    assert Volume.fields.pool.type.type is Pool

def test_creation(infinibox, volume, pool):
    pool = infinibox.pools.create()
    kwargs = {'name': 'some_volume_name',
              'size': 2 * GB,
              'pool_id': pool.id,
              'provisioning': 'THIN'}
    volume = create_volume(infinibox, **kwargs)

    assert volume.get_name() == kwargs['name']
    assert volume.get_size() == kwargs['size']
    assert volume.get_pool().id == kwargs['pool_id']
    assert volume.get_provisioning() == kwargs['provisioning']


def test_get_name(infinibox, volume, pool):
    vol_name = 'some_volume_name'
    volume = infinibox.volumes.create(name=vol_name, pool=pool)

    assert volume.get_name() == vol_name
    volume.delete()
    assert (not volume.is_in_system())


def test_update_name(infinibox, volume):
    new_name = 'some_volume_name'
    volume.update_name(new_name)
    assert volume.get_name() == new_name


def get_all_volumes(infinibox):
    return list(infinibox.volumes.get_all())


def test_get_all(infinibox, volume):
    orig_volumes = get_all_volumes(infinibox)
    new_pool = create_pool(infinibox)
    new_volume = create_volume(infinibox, pool=new_pool)
    curr_volumes = get_all_volumes(infinibox)

    assert len(curr_volumes) == (len(orig_volumes) + 1)
    assert volume in orig_volumes
    assert new_volume._cache['pool_id'] == new_pool.id


def test_get_pool(infinibox, volume, pool):
    assert pool == volume.get_pool()


def _create_and_validate_children(parent_obj, child_type):
    creation_func = getattr(parent_obj, 'create_' + child_type)
    children = [creation_func(name) for name in ['test_' + child_type, None]]
    is_right_type = lambda child: getattr(child, 'is_' + child_type)()
    validate_child = lambda child: is_right_type(
        child) and child.get_parent() == parent_obj
    assert all(map(validate_child, children))
    get_children_func = getattr(parent_obj, "get_{0}s".format(child_type))
    assert set(children) == set(get_children_func())
    return children


def test_clones_and_snapshots(infinibox, volume):
    assert volume.is_master_volume()
    assert volume.get_parent() is None
    assert not volume.has_children()

    snapshots = _create_and_validate_children(volume, 'snapshot')
    snap = snapshots[-1]
    clones = _create_and_validate_children(snap, 'clone')
    assert volume.has_children()

    for obj in clones + snapshots:
        obj.delete()
        assert not obj.is_in_system()
        assert volume.is_in_system()
    volume.refresh()
    assert (not volume.has_children())


def test_snapshot_creation_time(infinibox, volume):
    snap = volume.create_snapshot()

    assert isinstance(snap.get_creation_time(), arrow.Arrow)

@pytest.mark.parametrize('current_time', [1406113997.675789, 1406114887.452333, time.time()])
def test_created_at_field_type_conversion(current_time):
    now = arrow.get(int(current_time * 1000) / 1000.0)
    translator = MillisecondsDatetimeTranslator()
    converted = translator.from_api(translator.to_api(now))
    assert converted == _rounded_to_millsecs(now)

def _rounded_to_millsecs(arrow_timestamp):
    return arrow.get(int(arrow_timestamp.float_timestamp * 1000) / 1000.0)

def test_snapshot_creation_time_filtering(infinibox, volume):
    flux.current_timeline.sleep(1) # set a differentiator between volume creation time and snapshot time
    snap = volume.create_snapshot()
    query = infinibox.volumes.find(infinibox.volumes.fields.created_at < snap.get_creation_time())

    for vol in query:
        found = True
        assert vol != snap
    assert found

def test_restore(infinibox, volume):
    snapshot = volume.create_snapshot()

    assert volume.is_master_volume()
    assert snapshot.is_snapshot()

    volume.restore(snapshot)
    last_event = infinibox.events.get_last_event()
    assert last_event['code'] == 'VOLUME_RESTORE'

    snapshot.delete()
    assert (not snapshot.is_in_system())


def test_get_not_exist_attribute(infinibox, volume):
    with pytest.raises(APICommandFailed) as caught:
        infinibox.api.get('volumes/2/bla')
    received_error = caught.value.response.get_error()
    assert isinstance(received_error, dict)


def test_unique_key(infinibox, volume):
    assert volume.get_unique_key() is not None


def test_invalid_child_operation(infinibox, volume):
    with pytest.raises(InvalidOperationException):
        volume.create_clone()

    flux.current_timeline.sleep(5)
    snapshot = volume.create_snapshot()
    with pytest.raises(InvalidOperationException):
        snapshot.create_snapshot()


def test_object_creation_hooks_for_child_volumes(infinibox, volume):
    hook_ident = 'unittest_ident'
    l = []
    fork_callbacks = []

    def save_fork_callback(hook_name, **kwargs):
        fork_callbacks.append(hook_name)
    def hook_callback(hook_type, **kwargs):
        obj_name = kwargs['data']['name']
        l.append('{0}_{1}'.format(hook_type, obj_name))
    gossip.register(partial(hook_callback, 'pre'),
                    'infinidat.pre_object_creation', hook_ident)
    gossip.register(partial(hook_callback, 'failure'),
                    'infinidat.object_operation_failure', hook_ident)
    gossip.register(partial(hook_callback, 'post'),
                    'infinidat.post_object_creation', hook_ident)
    for fork_hook in [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]:
        gossip.register(partial(save_fork_callback, fork_hook), fork_hook)

    snapshot = volume.create_snapshot('a_snap')
    assert l == ['pre_a_snap', 'post_a_snap']
    assert fork_callbacks == [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]

    snapshot.create_clone('a_clone')
    assert l == ['pre_a_snap', 'post_a_snap', 'pre_a_clone', 'post_a_clone']
    assert fork_callbacks == [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]*2

    gossip.unregister_token(hook_ident)


def test_create_many(infinibox, pool):

    name = 'some_name'
    vols = infinibox.volumes.create_many(pool=pool, count=5, name=name)

    assert len(vols) == 5

    for index, vol in enumerate(vols, start=1):
        assert vol.get_name() == '{0}_{1}'.format(name, index)
