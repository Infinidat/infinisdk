import operator
from infinipy2.core import *
from ..utils import TestCase
from ..utils import api_scenario, FakeSystem
from urlobject import URLObject

class QueryExecutionTest(TestCase):
    def setUp(self):
        super(QueryExecutionTest, self).setUp()
        self.system = FakeSystem()
        self.system.start_api_scenario("izbox_handshake")
        self.addCleanup(self.system.end_api_scenario)

    def test_querying_length(self):
        all_filesystems = FileSystem.find(self.system)
        self.assertEquals(len(all_filesystems), 5)


class QueryTest(TestCase):
    def setUp(self):
        super(QueryTest, self).setUp()
        self.system = FakeSystem()
        self.field = FileSystem.fields.quota

    def test_querying_equal(self):
        for query in [
                FileSystem.find(self.system, id=2),
                FileSystem.find(self.system, FileSystem.fields.id==2),
        ]:
            self.assert_query_equals(query, "id=eq%3A2")

    def test_querying_ge(self):
        self.assert_query_equals(FileSystem.find(self.system, self.field >= "X"), "quota_in_bytes=ge%3AX")

    def test_querying_le(self):
        self.assert_query_equals(FileSystem.find(self.system, self.field <= "X"), "quota_in_bytes=le%3AX")

    def test_querying_gt(self):
        self.assert_query_equals(FileSystem.find(self.system, self.field > "X"), "quota_in_bytes=gt%3AX")

    def test_querying_lt(self):
        self.assert_query_equals(FileSystem.find(self.system, self.field < "X"), "quota_in_bytes=lt%3AX")

    def test_sorting(self):
        self.assert_query_equals(
            FileSystem.find(self.system).sort(-FileSystem.fields.quota), "sort=-quota_in_bytes")
        self.assert_query_equals(
            FileSystem.find(self.system).sort(+FileSystem.fields.quota), "sort=quota_in_bytes")
        self.assert_query_equals(
            FileSystem.find(self.system).sort(FileSystem.fields.quota), "sort=quota_in_bytes")

    def test_sorting_multiple(self):
        self.assert_query_equals(
            FileSystem.find(self.system).sort(-FileSystem.fields.quota, +FileSystem.fields.id), "sort=-quota_in_bytes%2Cid")

    def test_only_fields(self):
        # NOTE: uses api name!
        self.assert_query_equals(
            FileSystem.find(self.system).only_fields(["quota"]), "fields=quota_in_bytes")

    def assert_query_equals(self, q, expected):
        self.assertEquals(
            q.query, "/api/rest/filesystems?" + expected)

class FileSystem(SystemObject):
    FIELDS = [
        Field("id", type=int),
        Field("quota", api_name="quota_in_bytes"), # we need this to check name translation
    ]
