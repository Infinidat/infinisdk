from infinipy2._compat import xrange, iteritems
from infinipy2.core import CapacityType
from capacity import TB, KiB, Capacity
from ..conftest import create_volume, create_pool


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

    assert pool._cache['name'] == kwargs['name']
    assert pool._cache['physical_capacity'] == kwargs['physical_capacity']
    assert pool._cache['virtual_capacity'] == kwargs['virtual_capacity']

    pool.delete()
    assert (not pool.is_in_system())


def test_get_name(infinibox, pool):
    pool_name = 'some_pool_name'
    pool = infinibox.pools.create(name=pool_name)

    assert pool.get_name() == pool_name
    pool.delete()
    assert (not pool.is_in_system())


def test_update_name(infinibox, pool):
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
    volumes = [create_volume(infinibox, pool_id=pool.id) for i in xrange(5)]
    assert list(pool.get_volumes()) == volumes
