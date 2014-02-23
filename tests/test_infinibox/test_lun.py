from tests.utils import InfiniBoxTestCase


class LogicalUnitTest(InfiniBoxTestCase):
    def setUp(self):
        super(LogicalUnitTest, self).setUp()
        self.host = self.system.hosts.create()
        self.addCleanup(self.host.delete)

        self.cluster = self.system.clusters.create()
        self.addCleanup(self.cluster.delete)

    def test_no_luns_mapped(self):
        luns = self.host.get_luns()
        self.assertEquals(len(luns), 0)

    def test_map_volume_to_cluster(self):
        volume = self._create_volume()
        self.cluster.map_volume(volume)

        luns = self.cluster.get_luns()
        self.assertEquals(len(luns), 1)

        lu = list(luns)[0]
        self.assertEquals(lu.get_volume(), volume)
        volume_lun = volume.get_lun()
        self.assertEquals(lu, volume_lun)
        self.assertEquals(lu, luns[int(volume_lun)])
        self.assertIs(lu.get_host(), None)
        self.assertEquals(lu.get_cluster(), self.cluster)

        lu.unmap()
        self.assertEquals(len(self.cluster.get_luns()), 0)

    def test_map_volume_to_host(self):
        volume = self._create_volume()
        self.host.map_volume(volume)

        luns = self.host.get_luns()
        self.assertEquals(len(luns), 1)

        lu = list(luns)[0]
        self.assertEquals(lu.get_lun(), int(lu))
        volume_lun = volume.get_lun()
        self.assertEquals(lu.get_volume(), volume)
        self.assertEquals(lu, luns[int(volume_lun)])
        self.assertEquals(lu, volume.get_lun())
        self.assertIs(lu.get_cluster(), None)
        self.assertEquals(lu.get_host(), self.host)

        lu.unmap()
        self.assertEquals(len(self.host.get_luns()), 0)

    def test_multiple_luns_mapping_objects(self):
        host_volume = self._create_volume()
        self.host.map_volume(host_volume)

        cluster_volume = self._create_volume()
        self.cluster.map_volume(cluster_volume)

        host_lus = self.host.get_luns()
        cluster_lus = self.cluster.get_luns()

        self.assertEquals(len(host_lus), 1)
        self.assertEquals(len(cluster_lus), 1)

        host_lu = list(host_lus)[0]
        self.assertEquals(list(host_lus[host_volume])[0], host_lu)

        cluster_lu = list(cluster_lus)[0]
        self.assertEquals(list(cluster_lus[cluster_volume])[0], cluster_lu)

        with self.assertRaises(KeyError):
            cluster_lus[host_volume]

        self.assertEquals(cluster_lus.get(host_lu.get_lun(), None), None)
        self.assertEquals(host_lus.get(host_lu.get_lun(), None), host_lu)

        self.assertFalse(cluster_lu in host_lus)

        self.assertNotEqual(host_lu, cluster_lu)

        host_lu.delete()
        cluster_lu.delete()
