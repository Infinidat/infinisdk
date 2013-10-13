from ..utils import TestCase
from capacity import GB

class FilesystemTest(TestCase):

    API_SCENARIOS = ["izbox_queries", "izbox_fs_update"]

    def test_filesystem_get_set_quota(self):
        fs = self.system.objects.filesystems.object_type(self.system, {"id": 151})
        self.assertEquals(fs.get_quota(), 2*GB)
        fs.update_quota(3*GB)

