from tests.utils import InfiniBoxTestCase
from infinipy2._compat import iteritems
from infinipy2.core import CapacityType
from infinipy2.core.exceptions import APICommandFailed
from capacity import GB


class VolumeTest(InfiniBoxTestCase):
    def setUp(self):
        super(VolumeTest, self).setUp()
        self.volume = self._create_volume()

    def test_creation(self):
        pool = self.system.pools.create()
        self.addCleanup(pool.delete)
        kwargs = {'name': 'some_volume_name',
                  'size': 2*GB,
                  'pool_id': pool.id,
                  'provtype': 'THIN'}
        volume = self._create_volume(**kwargs)
        kwargs.pop('provtype')  #FIXME: Remove this line, after infinibox implement it...
        kwargs['size'] = CapacityType.translator.to_api(kwargs['size'])
        for k, v in iteritems(kwargs):
            self.assertEqual(volume._cache[k], v)

    def test_get_name(self):
        vol_name = 'some_volume_name'
        pool = self._create_pool()
        volume = self.system.volumes.create(name=vol_name, pool=pool)

        self.assertEqual(volume.get_name(), vol_name)
        volume.delete()
        self.assertFalse(volume.is_in_system())

    def test_update_name(self):
        new_name = 'some_volume_name'
        self.volume.update_name(new_name)
        self.assertEqual(self.volume.get_name(), new_name)

    def _get_all_volumes(self):
        return list(self.system.volumes.get_all())

    def test_get_all(self):
        orig_volumes = self._get_all_volumes()
        new_pool = self._create_pool()
        new_volume = self._create_volume(pool=new_pool)
        curr_volumes = self._get_all_volumes()

        self.assertEqual(len(curr_volumes), len(orig_volumes)+1)
        self.assertIn(self.volume, orig_volumes)
        self.assertEqual(new_volume._cache['pool_id'], new_pool.id)

    def test_get_pool(self):
        pool = self._create_pool()
        vol = self._create_volume(pool=pool)
        self.assertEqual(pool, vol.get_pool())

    def _create_and_validate_children(self, parent_obj, child_type):
        creation_func = getattr(parent_obj, 'create_'+child_type)
        children = [creation_func(name) for name in ['test_'+child_type, None]]
        is_right_type = lambda child: getattr(child, 'is_'+child_type)()
        validate_child = lambda child: is_right_type(child) and child.get_parent() == parent_obj
        self.assertTrue(all(map(validate_child, children)))
        get_children_func = getattr(parent_obj, "get_{0}s".format(child_type))
        self.assertEqual(set(children), set(get_children_func()))
        return children

    def test_clones_and_snapshots(self):
        self.assertTrue(self.volume.is_master_volume())
        self.assertIs(self.volume.get_parent(), None)

        snapshots = self._create_and_validate_children(self.volume, 'snapshot')
        snap = snapshots[-1]
        clones = self._create_and_validate_children(snap, 'clone')

        for obj in clones+snapshots:
            obj.delete()
            self.assertFalse(obj.is_in_system())
            self.assertTrue(self.volume.is_in_system())

    def test_restore(self):
        self.skipTest('Not Implemented Yet')
        snapshot_data = self.volume.create_snapshot()
        snapshot = self.system.volumes.get_by_id_lazy(snapshot_data.get_json()['result'])

        self.assertTrue(self.volume.is_master_volume())
        self.assertTrue(snapshot.is_snapshot())

        self.volume.restore(snapshot)
        self.assertEqual(self.volume.get_field('data'), snapshot.get_field('data'))

    def test_get_not_exist_attribute(self):
        with self.assertRaises(APICommandFailed) as caught:
            self.system.api.get('volumes/2/bla')
        received_error = caught.exception.response.get_error()
        self.assertTrue(isinstance(received_error, dict))
