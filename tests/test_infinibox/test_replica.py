import pytest

from ..conftest import infinibox as _create_infinibox
from ..conftest import infinibox_simulator as _create_infinibox_simlator
from ecosystem.mocks import MockedContext


def test_replica_creation(replica):
    pass


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


@pytest.mark.parametrize('retain_staging_area', [True, False])
def test_replica_change_role(replica, retain_staging_area):
    replica.suspend()
    assert replica.is_source()
    assert not replica.is_target()
    replica.change_role(retain_staging_area=retain_staging_area)
    assert not replica.is_source()
    assert replica.is_target()


def test_replica_has_local_entity(infinibox, replica, volume):
    assert replica.has_local_entity(volume)
    assert not replica.has_local_entity(infinibox.pools.create())


def test_volume_get_replicas(replica, volume):
    assert volume.get_replicas() == [replica]


def test_replica_suspend_resume(replica):
    assert not replica.is_suspended()
    replica.suspend()
    assert replica.is_suspended()
    replica.resume()
    assert not replica.is_suspended()


@pytest.fixture
def replica(infinibox, secondary_infinibox, link, replica_creation_kwargs):
    return infinibox.replicas.create(
        link=link, **replica_creation_kwargs)


@pytest.fixture
def replica_creation_kwargs(volume, create_remote, secondary_pool):
    entity_pair = {
        'local_entity_id': volume.id,
    }

    if create_remote:
        entity_pair.update({
            'target_base_action': 'CREATE',
        })
    else:
        entity_pair.update({
            'remote_entity_id': secondary_pool.system.volumes.create(pool=secondary_pool).id,
            'target_base_action': 'NO_BASE_DATA',
        })

    return {
        'remote_pool_id': secondary_pool.id,
        'entity_pairs': [entity_pair],
    }


@pytest.fixture
def secondary_pool(secondary_infinibox):
    return secondary_infinibox.pools.create()


@pytest.fixture(params=[True, False])
def create_remote(request):
    return request.param
