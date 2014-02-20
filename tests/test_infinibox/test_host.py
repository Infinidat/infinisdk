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

    def test_get_cluster(self):
        cluster = self.system.clusters.create()
        self.addCleanup(cluster.delete)
        cluster.add_host(self.host)
        self.assertEqual(self.host.get_cluster(), cluster)

    def test_ports_operations(self):
        self.skipTest('Does infinibox support this?')
        fc_address = "00:01:02:03:04:05:06:07"
        iscsi_address = "07:06:05:04:03:02:01:00"

        self.assertEqual(self.host.get_field("ports"), [])
        self.host.add_fc_port(fc_address)
        self.host.add_iscsi_port(iscsi_address)

        self.assertEqual([fc_address], self.host.get_fc_ports())
        self.assertEqual([iscsi_address], self.host.get_iscsi_ports())

        self.host.remove_fc_port(fc_address)
        self.assertEqual([], self.host.get_fc_ports())
        self.assertEqual([iscsi_address], self.host.get_iscsi_ports())

        self.host.remove_iscsi_port(iscsi_address)
        self.assertEqual([], self.host.get_fc_ports())
        self.assertEqual([], self.host.get_iscsi_ports())
