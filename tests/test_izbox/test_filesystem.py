from ..utils import TestCase
from capacity import GB

class FilesystemTest(TestCase):

    API_SCENARIOS = ["izbox_queries", "izbox_fs_update"]

    def setUp(self):
        super(FilesystemTest, self).setUp()
        self.fs = self.system.objects.filesystems.get_by_id_lazy(151)

    def test_filesystem_get_set_quota(self):
        self.assertEquals(self.fs.get_quota(), 2*GB)
        self.fs.update_quota(3*GB)

    def test_filesystem_get_set_name(self):
        self.assertEquals(self.fs.get_name(), "fs151")
        self.fs.update_name("new_name")

