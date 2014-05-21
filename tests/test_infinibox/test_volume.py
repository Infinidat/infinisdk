import gossip
from tests.utils import InfiniBoxTestCase
from infinipy2.core.exceptions import APICommandFailed, InvalidOperationException
from capacity import GB
from functools import partial


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
                  'provisioning': 'THIN'}
        volume = self._create_volume(**kwargs)

        self.assertEqual(volume.get_name(), kwargs['name'])
        self.assertEqual(volume.get_size(), kwargs['size'])
        self.assertEqual(volume.get_pool().id, kwargs['pool_id'])
        self.assertEqual(volume.get_provisioning(), kwargs['provisioning'])

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
        self.assertFalse(self.volume.has_children())

        snapshots = self._create_and_validate_children(self.volume, 'snapshot')
        snap = snapshots[-1]
        clones = self._create_and_validate_children(snap, 'clone')
        self.assertTrue(self.volume.has_children())

        for obj in clones+snapshots:
            obj.delete()
            self.assertFalse(obj.is_in_system())
            self.assertTrue(self.volume.is_in_system())
        self.assertFalse(self.volume.has_children())

    def test_restore(self):
        snapshot = self.volume.create_snapshot()

        self.assertTrue(self.volume.is_master_volume())
        self.assertTrue(snapshot.is_snapshot())

        self.volume.restore(snapshot)
        last_event = self.system.events.get_last_event()
        self.assertEqual(last_event['code'], 'VOLUME_RESTORE')

        snapshot.delete()
        self.assertFalse(snapshot.is_in_system())

    def test_get_not_exist_attribute(self):
        with self.assertRaises(APICommandFailed) as caught:
            self.system.api.get('volumes/2/bla')
        received_error = caught.exception.response.get_error()
        self.assertTrue(isinstance(received_error, dict))

    def test_unique_key(self):
        self.assertIsNot(self.volume.get_unique_key(), None)

    def test_invalid_child_operation(self):
        with self.assertRaises(InvalidOperationException):
            self.volume.create_clone()

        snapshot = self.volume.create_snapshot()
        with self.assertRaises(InvalidOperationException):
            snapshot.create_snapshot()

    def test_object_creation_hooks_for_child_volumes(self):
        hook_ident = 'unittest_ident'
        l = []
        def hook_callback(hook_type, **kwargs):
            obj_name = kwargs['data']['name']
            l.append('{0}_{1}'.format(hook_type, obj_name))
        gossip.register(partial(hook_callback, 'pre'), 'pre_object_creation', hook_ident)
        gossip.register(partial(hook_callback, 'failure'), 'object_operation_failure', hook_ident)
        gossip.register(partial(hook_callback, 'post'), 'post_object_creation', hook_ident)

        snapshot = self.volume.create_snapshot('a_snap')
        self.assertEquals(l, ['pre_a_snap', 'post_a_snap'])

        snapshot.create_clone('a_clone')
        self.assertEquals(l, ['pre_a_snap', 'post_a_snap', 'pre_a_clone', 'post_a_clone'])

        gossip.unregister_token(hook_ident)
