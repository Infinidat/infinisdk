import time
import arrow
from functools import partial

import flux
from capacity import GB

import gossip
import pytest
from infinisdk.core.translators_and_types import MillisecondsDatetimeTranslator
from infinisdk.core.exceptions import (APICommandFailed,
                                       InvalidOperationException)
from infinisdk.infinibox.dataset import _BEGIN_FORK_HOOK, _FINISH_FORK_HOOK, _CANCEL_FORK_HOOK
from ..conftest import create_pool


def test_creation(pool, data_entity):
    kwargs = {'name': 'some_data_entity_name',
              'size': 2*GB,
              'pool_id': pool.id,
              'provisioning': 'THIN'}
    data_entity_binder = data_entity.get_collection()
    obj = data_entity_binder.create(**kwargs)

    assert obj.get_name() == kwargs['name']
    assert obj.get_size() == kwargs['size']
    assert obj.get_pool().id == kwargs['pool_id']
    assert obj.get_provisioning() == kwargs['provisioning']
    obj.delete()
    assert not obj.is_in_system()


def test_update_name(data_entity):
    new_name = 'some_new_name'
    assert data_entity.get_name() != new_name
    data_entity.update_name(new_name)
    assert data_entity.get_name() == new_name


def test_is_master(data_entity):
    assert data_entity.is_master()


def test_resize(data_entity):
    delta = 2 * GB
    initial_size = data_entity.get_size()
    data_entity.resize(delta)
    assert data_entity.get_size() == initial_size + delta
    data_entity.resize(delta)
    assert data_entity.get_size() == initial_size + delta * 2
    with pytest.raises(APICommandFailed):
        data_entity.resize(-delta)


def test_get_all(data_entity):
    data_entity_binder = data_entity.get_collection()
    orig_entities = list(data_entity_binder.get_all())
    new_pool = create_pool(data_entity.system)
    new_entity = data_entity_binder.create(pool=new_pool)
    curr_entities = list(data_entity_binder.get_all())

    assert len(curr_entities) == (len(orig_entities) + 1)
    assert data_entity in orig_entities
    assert new_entity in curr_entities
    assert new_entity not in orig_entities
    assert new_entity.get_pool(from_cache=True) == new_pool


def test_get_pool(data_entity, pool):
    assert pool == data_entity.get_pool()


def test_snapshot_creation_time(infinibox, data_entity):
    snap = data_entity.create_snapshot()
    assert isinstance(snap.get_creation_time(), arrow.Arrow)


def _create_and_validate_children(parent_obj, child_type):
    creation_func = getattr(parent_obj, 'create_' + child_type)
    children = [creation_func(name) for name in ['test_' + child_type, None]]
    is_right_type = lambda child: getattr(child, 'is_' + child_type)()
    validate_child = lambda child: is_right_type(child) and child.get_parent() == parent_obj
    assert all(map(validate_child, children))
    get_children_func = getattr(parent_obj, "get_{0}s".format(child_type))
    assert set(children) == set(get_children_func())
    assert set(child.get_parent() for child in children) == set([parent_obj])
    return children


def test_clones_and_snapshots(infinibox, data_entity):
    assert data_entity.is_master()
    assert not data_entity.has_children()
    assert data_entity.get_parent() is None

    snapshots = _create_and_validate_children(data_entity, 'snapshot')
    snap = snapshots[-1]
    clones = _create_and_validate_children(snap, 'clone')
    assert data_entity.has_children()

    for obj in clones + snapshots:
        obj.delete()
        assert not obj.is_in_system()
        assert data_entity.is_in_system()
    data_entity.refresh()
    assert (not data_entity.has_children())


@pytest.mark.parametrize('current_time', [1406113997.675789, 1406114887.452333])
def test_created_at_field_type_conversion(current_time):
    def _rounded_to_millsecs(arrow_timestamp):
        return arrow.get(int(round(arrow_timestamp.float_timestamp * 1000)) / 1000.0)
    now = arrow.get(int(current_time * 1000) / 1000.0)
    translator = MillisecondsDatetimeTranslator()
    converted = translator.from_api(translator.to_api(now))
    assert converted == _rounded_to_millsecs(now)


def test_snapshot_creation_time_filtering(data_entity):
    flux.current_timeline.sleep(1) # set a differentiator between filesystem creation time and snapshot time
    data_entity_binder = data_entity.get_collection()
    snap = data_entity.create_snapshot()
    query = data_entity_binder.find(data_entity_binder.fields.created_at < snap.get_creation_time())

    for fs in query:
        found = True
        assert fs != snap
    assert found

def test_get_not_exist_attribute(data_entity):
    with pytest.raises(APICommandFailed) as caught:
        data_entity.system.api.get(data_entity.get_this_url_path().add_path('bla'))
    received_error = caught.value.response.get_error()
    assert isinstance(received_error, dict)

def test_invalid_child_operation(data_entity):
    with pytest.raises(InvalidOperationException):
        data_entity.create_clone()

    flux.current_timeline.sleep(5)
    snapshot = data_entity.create_snapshot()
    with pytest.raises(InvalidOperationException):
        snapshot.create_snapshot()

def test_object_creation_hooks_for_child_entities(data_entity):
    hook_ident = 'unittest_ident'
    l = []
    fork_callbacks = []
    password = 'some_password'
    username = data_entity.system.users.create(role='ReadOnly', password=password).get_name()

    def save_fork_callback(hook_name, **kwargs):
        fork_callbacks.append(hook_name)

    def hook_callback(hook_type, **kwargs):
        obj_name = kwargs['data']['name']
        l.append('{0}_{1}'.format(hook_type, obj_name))

    def hook_failure_callback(**kwargs):
        l.append('failure')

    gossip.register(partial(hook_callback, 'pre'),
                    'infinidat.sdk.pre_object_creation', hook_ident)
    gossip.register(hook_failure_callback, 'infinidat.sdk.object_operation_failure', hook_ident)
    gossip.register(partial(hook_callback, 'post'),
                    'infinidat.sdk.post_object_creation', hook_ident)
    for fork_hook in [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK, _CANCEL_FORK_HOOK]:
        gossip.register(partial(save_fork_callback, fork_hook), fork_hook)

    snapshot = data_entity.create_snapshot('a_snap')
    assert l == ['pre_a_snap', 'post_a_snap']
    assert fork_callbacks == [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]

    snapshot.create_clone('a_clone')
    assert l == ['pre_a_snap', 'post_a_snap', 'pre_a_clone', 'post_a_clone']
    assert fork_callbacks == [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]*2

    with data_entity.system.api.get_auth_context(username, password):
        with pytest.raises(APICommandFailed):
            data_entity.create_snapshot('failed_snap')

    with data_entity.system.api.get_auth_context(username, password):
        with pytest.raises(APICommandFailed):
            snapshot.create_clone('failed_clone')

    assert l == ['pre_a_snap', 'post_a_snap',
                 'pre_a_clone', 'post_a_clone',
                 'pre_failed_snap', 'failure',
                 'pre_failed_clone', 'failure']
    assert fork_callbacks == [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]*2 + [_BEGIN_FORK_HOOK, _CANCEL_FORK_HOOK]*2

    gossip.unregister_token(hook_ident)


def test_data_restore(data_entity):
    hook_ident = 'unittest_restore_hook'
    callbacks = []
    expected = []
    password = 'some_password'
    username = data_entity.system.users.create(role='ReadOnly', password=password).get_name()

    @gossip.register('infinidat.sdk.pre_data_restore', token=hook_ident)
    def pre_restore(source, target):
        callbacks.append("pre_restore_{0}_from_{1}".format(target.id, source.id))

    @gossip.register('infinidat.sdk.post_data_restore', token=hook_ident)
    def post_restore(source, target):
        callbacks.append("post_restore_{0}_from_{1}".format(target.id, source.id))

    @gossip.register('infinidat.sdk.data_restore_failure', token=hook_ident)
    def restore_failure(source, target, exc):
        callbacks.append("restore_failure_{0}_from_{1}".format(target.id, source.id))

    snapshot = data_entity.create_snapshot('some_snapshot_to_restore_from')
    assert callbacks == []

    data_entity.restore(snapshot)

    last_events = data_entity.system.events.get_events()
    found_restore_event = False
    for last_event in last_events:
        if "{0}_RESTORE".format(data_entity.get_type_name().upper()) in last_event['code']:
            # Either VOLUME_RESTORE/FILESYSTEM_RESTORE for older versions, or VOLUME_RESTORED/FILESYSTEM_RESTORED for 2.0
            found_restore_event = True
            break
    assert found_restore_event

    args = (data_entity.id, snapshot.id)
    expected += ['pre_restore_{0}_from_{1}'.format(*args), 'post_restore_{0}_from_{1}'.format(*args)]
    assert callbacks == expected

    with data_entity.system.api.get_auth_context(username, password):
        with pytest.raises(APICommandFailed):
            data_entity.restore(snapshot)
    expected += ['pre_restore_{0}_from_{1}'.format(*args), 'restore_failure_{0}_from_{1}'.format(*args)]
    assert callbacks == expected

    gossip.unregister_token(hook_ident)


def test_get_children_snapshots_and_clones(data_entity):
    snap = data_entity.create_snapshot()
    clone = snap.create_clone()
    snap2 = clone.create_snapshot()

    assert set(data_entity.get_children()) == set(data_entity.get_snapshots()) == set([snap])
    assert set(snap.get_clones()) == set(snap.get_children()) == set([clone])
    assert set(clone.get_children()) == set(clone.get_snapshots()) == set([snap2])

    assert set(snap.get_snapshots()) == set()
    assert set(clone.get_clones()) == set()
