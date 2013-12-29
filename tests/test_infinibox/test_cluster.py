from tests.utils import InfiniBoxTestCase
from infinipy2._compat import iteritems


class ClusterTest(InfiniBoxTestCase):
    def setUp(self):
        super(ClusterTest, self).setUp()
        self.cluster = self.system.clusters.create()
        self.addCleanup(self.cluster.delete)

    def test_get_name(self):
        self.assertTrue(self.cluster.get_name().startswith('cluster_'))

    def test_update_name(self):
        curr_name = self.cluster.get_name()
        new_name = 'other_cluster_name'
        self.cluster.update_name(new_name)

        self.assertNotEqual(curr_name, new_name)
        self.assertEqual(self.cluster.get_name(), new_name)

    def test_creation(self):
        kwargs = {'name': 'some_cluster_name',}
        cluster = self.system.clusters.create(**kwargs)

        for k, v in iteritems(kwargs):
            self.assertEqual(cluster._cache[k], v)
        self.assertEqual(cluster.get_hosts(), [])

        cluster.delete()
        self.assertFalse(cluster.is_in_system())

    def test_hosts_operations(self):
        self.assertEqual(self.cluster.get_hosts(), [])
        host = self.system.hosts.create()
        self.addCleanup(host.delete)

        self.cluster.add_host(host)
        hosts = self.cluster.get_hosts()
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0], host)

        self.cluster.remove_host(host)
        hosts = self.cluster.get_hosts()
        self.assertEqual(len(hosts), 0)
