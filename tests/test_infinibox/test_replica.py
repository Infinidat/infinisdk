from datetime import timedelta

import pytest
from infinisdk.core.exceptions import (CannotGetReplicaState,
                                       InfiniSDKException, ObjectNotFound,
                                       TooManyObjectsFound, UnknownSystem)

from ..conftest import secondary_infinibox as secondary_infinibox_fx
from ..conftest import relevant_from_version
import flux

SECOND = SECONDS = timedelta(seconds=1)


@relevant_from_version('2.0')
def test_replica_creation(replica):  # pylint: disable=unused-argument
    pass


@relevant_from_version('2.0')
def test_replica_sync_interval(replica):
    interval = 30 * SECONDS
    replica.update_sync_interval(interval)
    assert interval == replica.get_sync_interval()


@relevant_from_version('2.0')
def test_replica_zero_sync_interval(replica):
    replica.update_sync_interval(0)
    assert replica.get_sync_interval() == timedelta(seconds=0)


@relevant_from_version('2.0')
def test_create_replica_with_link_name(infinibox, secondary_infinibox, link, replica_creation_kwargs):
    infinibox.register_related_system(secondary_infinibox)
    secondary_infinibox.register_related_system(infinibox)
    replica = infinibox.replicas.create(
        link=link.get_name(), **replica_creation_kwargs)

    assert replica.get_link() == link

@relevant_from_version('2.0')
def test_get_remote_entity_pairs(replica, remote_replica):
    local = replica.get_field('entity_pairs')
    remote = remote_replica.get_field('entity_pairs')
    assert local != remote
    assert remote == replica.get_remote_entity_pairs()


@relevant_from_version('2.0')
def test_replica_get_fields(replica):
    fields = replica.get_fields()
    assert isinstance(fields, dict)


@relevant_from_version('2.0')
@pytest.mark.parametrize('method_name', ['get_local_volume', 'get_local_entity'])
def test_replica_get_local_entity(replica, volume, method_name):
    method = getattr(replica, method_name)
    assert method() == volume


@relevant_from_version('2.0')
@pytest.mark.parametrize('method_name', ['get_local_volume', 'get_local_entity'])
def test_replica_get_local_entity_more_than_one(replica, method_name):
    method = getattr(replica, method_name)
    replica._cache['entity_pairs'].append(replica._cache['entity_pairs'][0])  # pylint: disable=protected-access
    with pytest.raises(TooManyObjectsFound):
        method()


@relevant_from_version('2.0')
@pytest.mark.parametrize('force_params', [True, False])
@pytest.mark.parametrize('retain_staging_area', [True, False])
def test_replica_deletion(replica, retain_staging_area, force_params):
    flux.current_timeline.sleep_wait_all_scheduled()
    kwargs = {}
    if force_params:
        kwargs.update(force_on_target=True, force_if_remote_error=True,
                      force_if_no_remote_credentials=True)
    if retain_staging_area:
        kwargs.update(retain_staging_area=True)
    volume = replica.get_local_volume()
    assert not volume.get_children()
    replica.delete(**kwargs)
    if retain_staging_area:
        assert volume.get_children()


@relevant_from_version('2.2')
def test_replica_deletion_unknown_system(replica, forge):
    def raise_unknown_system(safe=False):
        if safe:
            return None
        raise UnknownSystem()
    forge.replace_with(replica, 'get_remote_replica', raise_unknown_system)
    replica.delete()
    assert not replica.is_in_system()

@relevant_from_version('2.0')
@pytest.mark.parametrize('retain_staging_area', [True, False])
def test_replica_deletion_remote_first(replica, retain_staging_area):
    replica.get_remote_replica().delete(force_on_target=True)
    assert replica.is_in_system()
    replica.delete(retain_staging_area=retain_staging_area)

@relevant_from_version('2.0')
@pytest.mark.parametrize('create_remote_volume', [True, False])
def test_replicate_volume_shortcut(infinibox, secondary_infinibox, link, create_remote_volume, volume):
    remote_pool = secondary_infinibox.pools.create()
    kwargs = {}
    if create_remote_volume:
        kwargs['remote_pool'] = remote_pool
    else:
        remote_volume = kwargs['remote_volume'] = secondary_infinibox.volumes.create(
            pool=remote_pool)
    replica = infinibox.replicas.replicate_volume(volume, link=link, **kwargs)
    assert replica is not None

    [remote_replica] = secondary_infinibox.replicas
    if create_remote_volume:
        pass
    else:
        assert remote_replica.has_local_entity(remote_volume)


@relevant_from_version('2.0')
def test_replica_change_role(synced_replica):
    synced_replica.suspend()
    assert synced_replica.is_source()
    assert not synced_replica.is_target()
    synced_replica.change_role()
    assert not synced_replica.is_source()
    assert synced_replica.is_target()


@relevant_from_version('3.0')
def test_replica_user_suspended(replica):
    assert not replica.is_user_suspended()
    replica.suspend()
    assert replica.is_user_suspended()
    replica.resume()
    assert not replica.is_user_suspended()


@relevant_from_version('2.0')
def test_replica_change_role_with_entity_pairs(replica):
    pytest.skip('wait for sync before changing role')
    replica.get_remote_replica().change_role(entity_pairs=replica.get_entity_pairs())


@relevant_from_version('2.0')
def test_replica_has_local_entity(infinibox, replica, volume):
    assert replica.has_local_entity(volume)
    assert not replica.has_local_entity(infinibox.pools.create())


@relevant_from_version('2.0')
def test_volume_get_replicas(replica, volume):
    assert volume.get_replicas() == [replica]


@relevant_from_version('2.0')
def test_volume_get_replica_single(volume, replica):
    assert volume.get_replica() == replica


@relevant_from_version('2.0')
def test_is_rmr_source(volume, replica):  # pylint: disable=unused-argument
    volume.invalidate_cache()
    assert not volume.is_rmr_target()
    assert volume.is_rmr_source()


@relevant_from_version('2.0')
def test_is_replicated(volume, replica):
    volume.invalidate_cache()
    assert volume.is_replicated()
    replica.delete()
    volume.invalidate_cache()
    assert not volume.is_replicated()


@relevant_from_version('2.0')
def test_regtulard_volume_is_not_rmr_source_target(volume):
    assert not volume.is_rmr_source()
    assert not volume.is_rmr_target()


@relevant_from_version('2.0')
def test_is_rmr_target(volume, replica, secondary_volume):  # pylint: disable=unused-argument
    secondary_volume.invalidate_cache()
    assert secondary_volume.is_rmr_target()
    assert not secondary_volume.is_rmr_source()


@relevant_from_version('2.0')
def test_get_remote_system(replica, secondary_infinibox):
    assert replica.get_remote_system() == secondary_infinibox
    assert replica.get_remote_replica().get_remote_system() == replica.system


@relevant_from_version('2.0')
def test_remote_replica(request, replica, secondary_volume, secondary_infinibox):
    third_system = secondary_infinibox_fx(request)
    replica.system.register_related_system(third_system)
    remote_replica = replica.get_remote_replica()
    assert remote_replica.get_system().get_name() == secondary_infinibox.get_name()
    assert remote_replica.get_local_entity().get_id() == secondary_volume.get_id()
    assert remote_replica.is_target()
    assert remote_replica.get_state() is None
    with pytest.raises(CannotGetReplicaState):
        remote_replica.is_suspended()
    with pytest.raises(CannotGetReplicaState):
        remote_replica.is_active()


@relevant_from_version('2.0')
def test_remote_replica_without_remote_system(replica, secondary_infinibox):  # pylint: disable=unused-argument
    remote_replica = replica.get_remote_replica()
    replica.system.unregister_related_system(remote_replica.system)  # pylint: disable=protected-access
    remote_replica.system.unregister_related_system(replica.system)  # pylint: disable=protected-access
    flux.current_timeline.sleep_wait_all_scheduled()
    assert replica.is_idle()
    with pytest.raises(InfiniSDKException):
        replica.get_remote_replica()
    with pytest.raises(InfiniSDKException):
        remote_replica.get_remote_replica()
    assert not replica.is_suspended()
    with pytest.raises(InfiniSDKException):
        remote_replica.is_suspended()



@relevant_from_version('2.0')
def test_volume_get_replica_no_replicas(volume):
    with pytest.raises(ObjectNotFound):
        volume.get_replica()


@relevant_from_version('2.0')
def test_replica_suspend_resume(replica):
    assert not replica.is_suspended()
    replica.suspend()
    assert replica.is_suspended()
    replica.resume()
    assert not replica.is_suspended()

@relevant_from_version('2.0')
def test_replica_get_remote_entity(replica):
    local = replica.get_local_entity()
    remote = replica.get_remote_entity()
    assert local.system == replica.system
    assert remote.system != replica.system
    assert local != remote
    assert local.get_remote_entity() == remote

def test_get_remote_entity_no_replica(data_entity):
    assert data_entity.get_remote_entity() is None
    assert data_entity.get_remote_entities() == []
