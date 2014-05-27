from tests.utils import InfiniBoxTestCase
from infinipy2._compat import iteritems


class HostTest(InfiniBoxTestCase):
    def setUp(self):
        super(HostTest, self).setUp()
        self.host = self.system.hosts.create()
        self.addCleanup(self.host.delete)

    def test_get_name(self):
        self.assertTrue(self.host.get_name().startswith('host_'))

    def test_update_name(self):
        curr_name = self.host.get_name()
        new_name = 'some_host_name'
        self.host.update_name(new_name)

        self.assertNotEqual(curr_name, new_name)
        self.assertEqual(self.host.get_name(), new_name)

    def test_creation(self):
        kwargs = {'name': 'some_host_name',}
        host = self.system.hosts.create(**kwargs)
        self.addCleanup(host.delete)

        for k, v in iteritems(kwargs):
            self.assertEqual(host._cache[k], v)

        self.assertIs(host.get_cluster(), None)

    def test_get_cluster(self):
        cluster = self.system.clusters.create()
        self.addCleanup(cluster.delete)
        cluster.add_host(self.host)
        self.assertEqual(self.host.get_cluster(), cluster)

    def test_fc_port_operations(self):
        address1 = "00:01:02:03:04:05:06:07"
        address2 = "07:06:05:04:03:02:01:00"
        address1s = address1.replace(":","")
        address2s = address2.replace(":","")

        self.assertEqual(self.host.get_fc_ports(), [])
        self.host.add_fc_port(address1)
        self.host.add_fc_port(address2)

        self.assertEqual([address1s, address2s], self.host.get_fc_ports())

        self.host.remove_fc_port(address1)
        self.assertEqual([address2s], self.host.get_fc_ports())

        self.host.remove_fc_port(address2)
        self.assertEqual([], self.host.get_fc_ports())
