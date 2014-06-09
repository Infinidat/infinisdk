from functools import partial

from capacity import GB

import gossip
import pytest
from infinisdk.core.exceptions import (APICommandFailed,
                                       InvalidOperationException)

from ..conftest import create_pool, create_volume


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
    assert (not volume.has_children())


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

    snapshot = volume.create_snapshot()
    with pytest.raises(InvalidOperationException):
        snapshot.create_snapshot()


def test_object_creation_hooks_for_child_volumes(infinibox, volume):
    hook_ident = 'unittest_ident'
    l = []

    def hook_callback(hook_type, **kwargs):
        obj_name = kwargs['data']['name']
        l.append('{0}_{1}'.format(hook_type, obj_name))
    gossip.register(partial(hook_callback, 'pre'),
                    'infinidat.pre_object_creation', hook_ident)
    gossip.register(partial(hook_callback, 'failure'),
                    'infinidat.object_operation_failure', hook_ident)
    gossip.register(partial(hook_callback, 'post'),
                    'infinidat.post_object_creation', hook_ident)

    snapshot = volume.create_snapshot('a_snap')
    assert l == ['pre_a_snap', 'post_a_snap']

    snapshot.create_clone('a_clone')
    assert l == ['pre_a_snap', 'post_a_snap', 'pre_a_clone', 'post_a_clone']

    gossip.unregister_token(hook_ident)
