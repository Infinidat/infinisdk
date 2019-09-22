import flux
import pytest
from datetime import timedelta
from infinisdk.infinibox.components import InfiniBoxSystemComponents


@pytest.fixture
def secondary_volume(replica, secondary_infinibox):  # pylint: disable=unused-argument
    [returned] = secondary_infinibox.volumes
    return returned


@pytest.fixture
def replica(infinibox, secondary_infinibox, link, replica_creation_kwargs):
    infinibox.register_related_system(secondary_infinibox)
    secondary_infinibox.register_related_system(infinibox)
    return infinibox.replicas.create(
        link=link, **replica_creation_kwargs)

@pytest.fixture
def cg_replica(infinibox, secondary_infinibox, cg, secondary_pool, link):
    infinibox.register_related_system(secondary_infinibox)
    secondary_infinibox.register_related_system(infinibox)
    cg.add_member(infinibox.volumes.create(pool=cg.get_pool()))
    kwargs = {'link': link, 'remote_pool': secondary_pool}
    if not infinibox.compat.has_sync_replication():
        kwargs['sync_interval'] = timedelta(4000)
    return infinibox.replicas.replicate_cons_group(
        cg, **kwargs)

@pytest.fixture
def cg(infinibox, volume):
    return infinibox.cons_groups.create(pool=volume.get_pool())

@pytest.fixture
def synced_replica(infinibox, secondary_infinibox, link, replica_creation_kwargs):
    infinibox.register_related_system(secondary_infinibox)
    secondary_infinibox.register_related_system(infinibox)
    replica = infinibox.replicas.create(
        link=link, **replica_creation_kwargs)
    flux.current_timeline.sleep_wait_all_scheduled()
    return replica

@pytest.fixture
def remote_replica(replica, secondary_infinibox):  # pylint: disable=unused-argument
    [returned] = secondary_infinibox.replicas
    return returned


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

    kwargs = {
        'remote_pool_id': secondary_pool.id,
        'entity_pairs': [entity_pair],
    }
    if not volume.system.compat.has_sync_replication():
        kwargs['sync_interval'] = timedelta(4000)
    return kwargs


@pytest.fixture
def secondary_pool(secondary_infinibox):
    return secondary_infinibox.pools.create()


@pytest.fixture(params=[True, False])
def create_remote(request):
    return request.param

@pytest.fixture
def volume_qos_policy(infinibox):
    return infinibox.qos_policies.create(type='VOLUME', max_ops=1000000)


@pytest.fixture(params=InfiniBoxSystemComponents.types.get_names())
def component_collection(request, infinibox):
    type_name = request.param
    type_class = infinibox.components.types.get_type_by_name(type_name)
    return infinibox.components[type_class]


@pytest.fixture
def component(component_collection):
    return component_collection.choose()
