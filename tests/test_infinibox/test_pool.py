from tests.utils import InfiniBoxTestCase
from infinipy2._compat import xrange, iteritems
from infinipy2.core import CapacityType
from capacity import TB, KiB,Capacity


class PoolTest(InfiniBoxTestCase):
    def setUp(self):
        super(PoolTest, self).setUp()
        self.pool = self._create_pool()

    def update_all_capacities_in_dict_to_api(self, d):
        capacity_translator = CapacityType.translator
        for k,v in iteritems(d):
            if isinstance(v, Capacity):
                d[k] = capacity_translator.to_api(v.roundup(6 * 64 * KiB))

    def test_creation(self):
        kwargs = {"name": "some_pool_name",
                  "virtual_capacity":  3*TB,
                  "physical_capacity": 3*TB}
        pool = self.system.pools.create(**kwargs)

        self.update_all_capacities_in_dict_to_api(kwargs)

        self.assertEqual(pool._cache['name'], kwargs['name'])
        self.assertEqual(pool._cache['virtual_capacity'],
                         kwargs['virtual_capacity'])

        pool.delete()
        self.assertFalse(pool.is_in_system())

    def test_get_name(self):
        pool_name = 'some_pool_name'
        pool = self.system.pools.create(name=pool_name)

        self.assertEqual(pool.get_name(), pool_name)
        pool.delete()
        self.assertFalse(pool.is_in_system())

    def test_update_name(self):
        new_name = 'some_pool_name'
        self.pool.update_name(new_name)
        self.assertEqual(self.pool.get_name(), new_name)

    def _get_all_pools(self):
        return list(self.system.pools.get_all())

    def test_get_all(self):
        orig_pools = self._get_all_pools()
        new_pool = self._create_pool()
        curr_pools = self._get_all_pools()

        self.assertEqual(len(curr_pools), len(orig_pools)+1)
        self.assertIn(self.pool, orig_pools)
        self.assertEqual(curr_pools[-1], new_pool)

    def test_get_volumes(self):
        volumes = [self._create_volume(pool_id=self.pool.id) for i in xrange(5)]
        self.assertEqual(list(self.pool.get_volumes()), volumes)
