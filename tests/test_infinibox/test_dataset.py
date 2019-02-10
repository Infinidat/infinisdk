from functools import partial

import arrow
import flux
import gossip
import pytest
from capacity import GB, Capacity, KiB
from infinisdk.core.q import Q
from infinisdk.core.exceptions import APICommandFailed
from infinisdk.core.translators_and_types import MillisecondsDatetimeTranslator
from infinisdk.infinibox.dataset import (_BEGIN_FORK_HOOK, _CANCEL_FORK_HOOK,
                                         _FINISH_FORK_HOOK)

from ..conftest import create_pool, relevant_from_version
FILESYSTEM_SIZE_GRANULARITY = 64 * KiB

def test_creation(pool, data_entity):
    kwargs = {'name': 'some_data_entity_name',
              'size': 2*GB,
              'pool_id': pool.id,
              'provisioning': 'THIN'}
    data_entity_binder = data_entity.get_collection()
    obj = data_entity_binder.create(**kwargs)

    assert obj.get_name() == kwargs['name']
    if isinstance(data_entity, data_entity.system.filesystems.object_type):
        assert obj.get_size() == kwargs['size'].roundup(FILESYSTEM_SIZE_GRANULARITY)
    else:
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


@relevant_from_version('5.0')
def test_resize(data_entity):
    is_filesystem = data_entity.get_type_name() == 'filesystem'
    delta = 2 * GB
    initial_size = data_entity.get_size()
    data_entity.resize(delta)
    expected_size = initial_size + delta
    if is_filesystem:
        expected_size = expected_size.roundup(FILESYSTEM_SIZE_GRANULARITY)
    assert data_entity.get_size() == expected_size
    data_entity.resize(delta)
    expected_size = initial_size + delta * 2
    if is_filesystem:
        expected_size = expected_size.roundup(FILESYSTEM_SIZE_GRANULARITY)
    assert data_entity.get_size() == expected_size
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


def test_snapshot_creation_time(data_entity):
    snap = data_entity.create_snapshot()
    assert isinstance(snap.get_creation_time(), arrow.Arrow)


def _create_and_validate_children(parent_obj, child_type):
    # pylint: disable=protected-access
    children = [parent_obj.create_snapshot(name)
                for name in ['test_{}_{}'.format(child_type, parent_obj.get_id()), None]]
    expected_type = parent_obj._get_snapshot_type() if child_type == 'snapshot' else 'CLONE'
    is_right_type = lambda child: child.get_type() == expected_type
    validate_child = lambda child: is_right_type(child) and child.get_parent() == parent_obj
    assert all(validate_child(child) for child in  children)
    get_children_func = getattr(parent_obj, "get_{}s".format(child_type))
    assert set(children) == set(get_children_func())
    assert set(child.get_parent() for child in children) == set([parent_obj])
    return children


def test_clones_and_snapshots(infinibox, data_entity):
    assert data_entity.is_master()
    assert not data_entity.has_children()
    assert data_entity.get_parent() is None

    snapshots = _create_and_validate_children(data_entity, 'snapshot')
    snap = snapshots[-1]
    child_type = 'snapshot' if  infinibox.compat.has_writable_snapshots() else 'clone'
    clones = _create_and_validate_children(snap, child_type)
    assert data_entity.has_children()

    for obj in clones + snapshots:
        obj.delete()
        assert not obj.is_in_system()
        assert data_entity.is_in_system()
    data_entity.invalidate_cache()
    assert (not data_entity.has_children())


def test_create_child(infinibox, data_entity):
    child1 = data_entity.create_snapshot()
    assert child1.get_parent() == data_entity

    child2 = child1.create_snapshot()
    assert child2.get_parent() == child1

    if infinibox.compat.has_writable_snapshots():
        child3 = data_entity.create_snapshot(write_protected=False)
        assert not child3.get_field('write_protected')
        child4 = data_entity.create_snapshot(write_protected=True)
        assert child4.get_field('write_protected')
    else:
        with pytest.raises(AssertionError):
            child3 = data_entity.create_snapshot(write_protected=True)

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


def test_object_creation_hooks_for_child_entities(data_entity):
    hook_ident = 'unittest_ident'
    l = []
    fork_callbacks = []
    password = 'some_password'
    username = data_entity.system.users.create(role='ReadOnly', password=password).get_name()

    def save_fork_callback(hook_name, **kwargs):  # pylint: disable=unused-argument
        fork_callbacks.append(hook_name)

    def hook_callback(hook_type, **kwargs):
        obj_name = kwargs['data']['name']
        l.append('{}_{}'.format(hook_type, obj_name))

    def hook_failure_callback(**kwargs):  # pylint: disable=unused-argument
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

    snapshot.create_snapshot('a_clone')
    assert l == ['pre_a_snap', 'post_a_snap', 'pre_a_clone', 'post_a_clone']
    assert fork_callbacks == [_BEGIN_FORK_HOOK, _FINISH_FORK_HOOK]*2

    with data_entity.system.api.get_auth_context(username, password):
        with pytest.raises(APICommandFailed):
            data_entity.create_snapshot('failed_snap')

    with data_entity.system.api.get_auth_context(username, password):
        with pytest.raises(APICommandFailed):
            snapshot.create_snapshot('failed_clone')

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
    def pre_restore(source, target):  # pylint: disable=unused-variable
        callbacks.append("pre_restore_{}_from_{}".format(target.id, source.id))

    @gossip.register('infinidat.sdk.post_data_restore', token=hook_ident)
    def post_restore(source, target, **_):  # pylint: disable=unused-variable
        callbacks.append("post_restore_{}_from_{}".format(target.id, source.id))

    @gossip.register('infinidat.sdk.data_restore_failure', token=hook_ident)
    def restore_failure(source, target, exc):  # pylint: disable=unused-variable,unused-argument
        callbacks.append("restore_failure_{}_from_{}".format(target.id, source.id))

    snapshot = data_entity.create_snapshot('some_snapshot_to_restore_from')
    assert callbacks == []

    data_entity.restore(snapshot)

    last_events = data_entity.system.events.get_events()
    found_restore_event = False
    for last_event in last_events:
        if "{}_RESTORE".format(data_entity.get_type_name().upper()) in last_event['code']:
            # Either VOLUME_RESTORE/FILESYSTEM_RESTORE for older versions,
            # or VOLUME_RESTORED/FILESYSTEM_RESTORED for 2.0
            found_restore_event = True
            break
    assert found_restore_event

    args = (data_entity.id, snapshot.id)
    expected += ['pre_restore_{}_from_{}'.format(*args), 'post_restore_{}_from_{}'.format(*args)]
    assert callbacks == expected

    with data_entity.system.api.get_auth_context(username, password):
        with pytest.raises(APICommandFailed):
            data_entity.restore(snapshot)
    expected += ['pre_restore_{}_from_{}'.format(*args), 'restore_failure_{}_from_{}'.format(*args)]
    assert callbacks == expected

    gossip.unregister_token(hook_ident)


def test_get_capacity_field_with_null_value(data_entity):
    assert isinstance(data_entity.get_size(), Capacity)
    data_entity.update_field_cache({'size': None})
    assert data_entity.get_size(from_cache=True) is None


def test_calculate_reclaimable_space(data_entity):
    assert isinstance(data_entity.calculate_reclaimable_space(), Capacity)


@relevant_from_version('3.0')
def test_calculate_entities_reclaimable_space(data_entity):
    snap = data_entity.create_snapshot()
    assert isinstance(data_entity.get_collection().calculate_reclaimable_space([data_entity, snap]), Capacity)


def test_get_family_master(data_entity):
    assert data_entity.get_family_master() is data_entity
    child = data_entity.create_snapshot()
    assert child.get_family_master() == data_entity
    assert child.get_family_master().get_id() == data_entity.get_id()


@relevant_from_version('3.0')
def test_compression_enabled(data_entity):
    assert data_entity.is_compression_enabled()
    data_entity.disable_compression()
    assert not data_entity.is_compression_enabled()
    data_entity.enable_compression()
    assert data_entity.is_compression_enabled()


@pytest.mark.parametrize("name", [None, 'some_name'])
def test_create_multiple_datasets(data_entity, name):
    count = 3
    binder = data_entity.get_binder()
    objs = binder.create_many(count=count, pool=data_entity.get_pool(), name=name)
    assert len(objs) == count

    if name is None:
        name = objs[0].get_name()[:-2]  # If name is None, it was autogenerated for the create_many command
        expected_prefix = 'vol' if data_entity.get_type_name() == 'volume' else 'fs'
        assert name.startswith(expected_prefix)

    for index, vol in enumerate(objs, start=1):
        assert vol.get_name() == '{}_{}'.format(name, index)
        assert vol.is_master()


def test_datasets_queries(infinibox, volume, filesystem):
    dataset_list = [volume, volume.create_snapshot(), filesystem, filesystem.create_snapshot()]
    assert set(infinibox.datasets.to_list()) == set(dataset_list)
    assert set(infinibox.datasets.find(type='MASTER').to_list()) == set([volume, filesystem])


def test_query_datasets_of_specific_pool(infinibox, pool, volume, filesystem):
    assert infinibox.datasets.find(pool=pool).to_list() == [volume, filesystem]
    assert infinibox.datasets.find(Q.pool == pool).to_list() == [volume, filesystem]


def test_query_by_field_api_name(infinibox, pool, volume, filesystem):
    assert infinibox.datasets.find(pool_id=pool.id).to_list() == [volume, filesystem]
    assert infinibox.volumes.find(pool_id=pool.id).to_list() == [volume]
    assert infinibox.filesystems.find(pool_id=pool.id).to_list() == [filesystem]

    assert infinibox.datasets.find(Q.pool_id == pool.id).to_list() == [volume, filesystem]
    assert infinibox.volumes.find(Q.pool_id == pool.id).to_list() == [volume]
    assert infinibox.filesystems.find(Q.pool_id == pool.id).to_list() == [filesystem]


@relevant_from_version('3.0')
def test_refresh_snapshot(data_entity):
    assert data_entity.is_master()
    child = data_entity.create_snapshot()
    with pytest.raises(AssertionError):
        data_entity.refresh_snapshot()
    child.refresh_snapshot()
