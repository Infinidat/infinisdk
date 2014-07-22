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
from infinisdk.infinibox.base_data_entity import _BEGIN_FORK_HOOK, _FINISH_FORK_HOOK
from infinisdk.infinibox.filesystem import Filesystem
from infinisdk.infinibox.pool import Pool
from infinisdk.infinibox.scsi_serial import SCSISerial

from ..conftest import create_pool, create_filesystem


def test_exporting(infinibox, filesystem):
    assert not filesystem.get_exports()
    export = filesystem.add_export()
    assert filesystem.get_exports()[0] == export
    assert len(filesystem.get_exports()) == 1
    assert export in infinibox.exports.get_all()
    export.delete()
    assert not filesystem.get_exports()
    assert export not in infinibox.exports.get_all()

def test_export_deletion(filesystem):
    filesystem.add_export()
    filesystem.add_export()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    filesystem.get_exports()[0].delete()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    filesystem.get_exports()[0].delete()
    filesystem.delete()

def test_filesystem_children_deletion(filesystem):
    snap = filesystem.create_snapshot()
    clone = snap.create_clone()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    with pytest.raises(APICommandFailed) as caught:
        snap.delete()
    clone.delete()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    snap.delete()
    filesystem.delete()

def test_field_types():
    assert Filesystem.fields.parent.type.type is Filesystem
    assert Filesystem.fields.pool.type.type is Pool

def test_creation(infinibox, filesystem, pool):
    pool = infinibox.pools.create()
    kwargs = {'name': 'some_filesystem_name',
              'size': 2 * GB,
              'pool_id': pool.id,
              'provisioning': 'THIN'}
    filesystem = create_filesystem(infinibox, **kwargs)

    assert filesystem.get_name() == kwargs['name']
    assert filesystem.get_size() == kwargs['size']
    assert filesystem.get_pool().id == kwargs['pool_id']
    assert filesystem.get_provisioning() == kwargs['provisioning']


def test_get_name(infinibox, filesystem, pool):
    fs_name = 'some_filesystem_name'
    filesystem = infinibox.filesystems.create(name=fs_name, pool=pool)

    assert filesystem.get_name() == fs_name
    filesystem.delete()
    assert (not filesystem.is_in_system())


def test_update_name(infinibox, filesystem):
    new_name = 'some_filesystem_name'
    filesystem.update_name(new_name)
    assert filesystem.get_name() == new_name


def get_all_filesystems(infinibox):
    return list(infinibox.filesystems.get_all())


def test_get_all(infinibox, filesystem):
    orig_filesystems = get_all_filesystems(infinibox)
    new_pool = create_pool(infinibox)
    new_filesystem = create_filesystem(infinibox, pool=new_pool)
    curr_filesystems = get_all_filesystems(infinibox)

    assert len(curr_filesystems) == (len(orig_filesystems) + 1)
    assert filesystem in orig_filesystems
    assert new_filesystem._cache['pool_id'] == new_pool.id


def test_get_pool(infinibox, filesystem, pool):
    assert pool == filesystem.get_pool()


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


def test_clones_and_snapshots(infinibox, filesystem):
    assert filesystem.is_master()
    assert filesystem.get_parent() is None
    assert not filesystem.has_children()

    snapshots = _create_and_validate_children(filesystem, 'snapshot')
    snap = snapshots[-1]
    clones = _create_and_validate_children(snap, 'clone')
    assert filesystem.has_children()

    for obj in clones + snapshots:
        obj.delete()
        assert not obj.is_in_system()
        assert filesystem.is_in_system()
    filesystem.refresh()
    assert (not filesystem.has_children())


def test_snapshot_creation_time(infinibox, filesystem):
    snap = filesystem.create_snapshot()

    assert isinstance(snap.get_creation_time(), arrow.Arrow)

@pytest.mark.parametrize('current_time', [1406113997.675789, 1406114887.452333, time.time()])
def test_created_at_field_type_conversion(current_time):
    now = arrow.get(int(current_time * 1000) / 1000.0)
    translator = MillisecondsDatetimeTranslator()
    converted = translator.from_api(translator.to_api(now))
    assert converted == _rounded_to_millsecs(now)

def _rounded_to_millsecs(arrow_timestamp):
    return arrow.get(int(arrow_timestamp.float_timestamp * 1000) / 1000.0)

def test_snapshot_creation_time_filtering(infinibox, filesystem):
    flux.current_timeline.sleep(1) # set a differentiator between filesystem creation time and snapshot time
    snap = filesystem.create_snapshot()
    query = infinibox.filesystems.find(infinibox.filesystems.fields.created_at < snap.get_creation_time())

    for fs in query:
        found = True
        assert fs != snap
    assert found

def test_restore(infinibox, filesystem):
    snapshot = filesystem.create_snapshot()

    assert filesystem.is_master()
    assert snapshot.is_snapshot()

    with pytest.raises(NotImplementedError) as caught:
        filesystem.restore(snapshot)

    snapshot.delete()
    assert (not snapshot.is_in_system())


def test_get_not_exist_attribute(infinibox, filesystem):
    with pytest.raises(APICommandFailed) as caught:
        infinibox.api.get('filesystems/2/bla')
    received_error = caught.value.response.get_error()
    assert isinstance(received_error, dict)


def test_unique_key(infinibox, filesystem):
    with pytest.raises(AttributeError):
        filesystem.get_unique_key()


def test_invalid_child_operation(infinibox, filesystem):
    with pytest.raises(InvalidOperationException):
        filesystem.create_clone()

    flux.current_timeline.sleep(5)
    snapshot = filesystem.create_snapshot()
    with pytest.raises(InvalidOperationException):
        snapshot.create_snapshot()


def test_object_creation_hooks_for_child_filesystems(infinibox, filesystem):
    hook_ident = 'unittest_ident'
    l = []
    fork_callbacks = []

    def save_fork_callback(hook_name, **kwargs):
        fork_callbacks.append(hook_name)
    def hook_callback(hook_type, **kwargs):
        obj_name = kwargs['data']['name']
        l.append('{0}_{1}'.format(hook_type, obj_name))
    gossip.register(partial(hook_callback, 'pre'),
                    'infinidat.sdk.pre_object_creation', hook_ident)
    gossip.register(partial(hook_callback, 'failure'),
                    'infinidat.sdk.object_operation_failure', hook_ident)
    gossip.register(partial(hook_callback, 'post'),
                    'infinidat.sdk.post_object_creation', hook_ident)
    for fork_hook in [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]:
        gossip.register(partial(save_fork_callback, fork_hook), fork_hook)

    snapshot = filesystem.create_snapshot('a_snap')
    assert l == ['pre_a_snap', 'post_a_snap']
    assert fork_callbacks == [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]

    snapshot.create_clone('a_clone')
    assert l == ['pre_a_snap', 'post_a_snap', 'pre_a_clone', 'post_a_clone']
    assert fork_callbacks == [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]*2

    gossip.unregister_token(hook_ident)

def test_get_children_snapshots_and_clones(infinibox, filesystem):
    snap = filesystem.create_snapshot()
    clone = snap.create_clone()
    snap2 = clone.create_snapshot()

    assert set(filesystem.get_children()) == set(filesystem.get_snapshots()) == set([snap])
    assert set(snap.get_clones()) == set(snap.get_children()) == set([clone])
    assert set(clone.get_children()) == set(clone.get_snapshots()) == set([snap2])

    assert set(snap.get_snapshots()) == set()
    assert set(clone.get_clones()) == set()
