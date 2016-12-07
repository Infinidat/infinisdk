import pytest
from infinisdk._compat import iteritems
from infinisdk.core import CapacityType
from capacity import TB, GB, KiB, Capacity, TiB
from ..conftest import create_volume, create_pool, create_filesystem, relevant_from_version


def update_all_capacities_in_dict_to_api(d):
    capacity_translator = CapacityType.translator
    for k, v in iteritems(d):
        if isinstance(v, Capacity):
            d[k] = capacity_translator.to_api(v.roundup(6 * 64 * KiB))


def test_creation(infinibox, pool):
    kwargs = {"name": "some_pool_name",
              "virtual_capacity":  3 * TB,
              "physical_capacity": 3 * TB}
    pool = infinibox.pools.create(**kwargs)

    update_all_capacities_in_dict_to_api(kwargs)

    # pylint: disable=protected-access
    assert pool._cache['name'] == kwargs['name']
    assert pool._cache['physical_capacity'] == kwargs['physical_capacity']
    assert pool._cache['virtual_capacity'] == kwargs['virtual_capacity']

    pool.delete()
    assert (not pool.is_in_system())


@pytest.mark.parametrize('max_extend_value', [-1, GB])
def test_max_extend_type(pool, max_extend_value):
    pool.update_max_extend(max_extend_value)
    should_be_capacity = max_extend_value != -1
    assert isinstance(pool.get_max_extend(), Capacity) == should_be_capacity


def test_get_name(infinibox, pool):
    pool_name = 'some_pool_name'
    pool = infinibox.pools.create(name=pool_name)

    assert pool.get_name() == pool_name
    pool.delete()
    assert (not pool.is_in_system())


def test_update_name(pool):
    new_name = 'some_pool_name'
    pool.update_name(new_name)
    assert pool.get_name() == new_name


def _get_all_pools(infinibox):
    return list(infinibox.pools.get_all())


def test_get_all(infinibox, pool):
    orig_pools = _get_all_pools(infinibox)
    new_pool = create_pool(infinibox)
    curr_pools = _get_all_pools(infinibox)

    assert len(curr_pools) == (len(orig_pools) + 1)
    assert pool in orig_pools
    assert curr_pools[(-1)] == new_pool


def test_get_volumes(infinibox, pool):
    volumes = [create_volume(infinibox, pool_id=pool.id) for _ in range(5)]
    assert list(pool.get_volumes()) == volumes

def test_get_filesystems(infinibox, pool):
    filesystems = [create_filesystem(infinibox, pool_id=pool.id) for _ in range(5)]
    assert list(pool.get_filesystems()) == filesystems

def test_get_master_volumes(infinibox, pool):
    volumes = [create_volume(infinibox, pool_id=pool.id) for _ in range(5)]
    snapshots = [vol.create_child() for vol in volumes]
    MasterType = 'MASTER'
    assert list(pool.get_volumes()) == volumes + snapshots
    assert list(pool.get_volumes(type=MasterType)) == volumes

def test_get_master_filesystems(infinibox, pool):
    filesystems = [create_filesystem(infinibox, pool_id=pool.id) for _ in range(5)]
    snapshots = [fs.create_child() for fs in filesystems]
    MasterType = 'MASTER'
    assert list(pool.get_filesystems()) == filesystems + snapshots
    assert list(pool.get_filesystems(type=MasterType)) == filesystems

def test_pool_capacity_fields_types(pool):
    for field in pool.FIELDS:
        field_name = field.name
        if field_name.endswith('capacity') or field_name.endswith('space'):
            assert field.type.type == Capacity
            assert field.type.api_type == int
            assert isinstance(pool.get_field(field_name), Capacity)

def test_lock_pool(pool):
    assert not(pool.is_limited() or pool.is_locked())
    pool.lock()
    assert pool.is_locked()
    pool.unlock()
    assert not pool.is_locked()

def test_pool_thresholds(infinibox):
    pool = infinibox.pools.create(virtual_capacity=TB, physical_capacity=TB)
    assert pool.get_allocated_physical_capacity() == 0
    assert not pool.is_over_warning_threshold()
    assert not pool.is_over_critical_threshold()

    infinibox.volumes.create(pool=pool, provisioning='THICK', size=850*GB)
    assert pool.is_over_warning_threshold()
    assert not pool.is_over_critical_threshold()

    infinibox.volumes.create(pool=pool, provisioning='THICK', size=100*GB)
    assert pool.is_over_warning_threshold()
    assert pool.is_over_critical_threshold()


@relevant_from_version('3.0')
def test_compression_enabled(data_entity):
    assert data_entity.is_compression_enabled()
    data_entity.disable_compression()
    assert not data_entity.is_compression_enabled()
    data_entity.enable_compression()
    assert data_entity.is_compression_enabled()


def test_forbid_multiple_capacity_for_creation(infinibox):
    with pytest.raises(AssertionError):
        infinibox.pools.create(capacity=TB, virtual_capacity=TB)
    with pytest.raises(AssertionError):
        infinibox.pools.create(capacity=TB, physical_capacity=TB)
    with pytest.raises(AssertionError):
        infinibox.pools.create(capacity=TB, virtual_capacity=TB, physical_capacity=TB)


def test_capacity_for_creation(infinibox):
    capacity = 3*TiB
    pool = infinibox.pools.create(capacity=capacity)
    assert pool.get_virtual_capacity() == capacity
    assert pool.get_physical_capacity() == capacity
