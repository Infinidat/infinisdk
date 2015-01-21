import pytest

from ..conftest import infinibox as _create_infinibox
from ..conftest import infinibox_simulator as _create_infinibox_simlator
from ecosystem.mocks import MockedContext


def test_replica_creation(replica):
    pass


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
            'remote_base_action': 'CREATE',
        })
    else:
        entity_pair.update({
            'remote_entity_id': secondary_pool.system.volumes.create(pool=secondary_pool).id,
            'remote_base_action': 'NO_BASE_DATA',
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
