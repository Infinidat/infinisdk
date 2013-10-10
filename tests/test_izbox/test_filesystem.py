from ..utils import TestCase
from capacity import GB

class FilesystemTest(TestCase):

    API_SCENARIOS = ["izbox_queries"]

    def test_filesystem_get_quota(self):
        fs = self.system.objects.filesystems.object_type(self.system, {"id": 1})
        self.assertEquals(fs.get_quota(), 2*GB)
