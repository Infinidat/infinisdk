import operator
from infinipy2.core import *
from infinipy2.core.exceptions import ObjectNotFound, TooManyObjectsFound
from infinipy2.izbox import IZBox
from infinipy2.izbox.filesystem import Filesystem
from ..utils import TestCase
from ..utils import api_scenario
from urlobject import URLObject

class QueryTestBase(TestCase):

    def setUp(self):
        super(QueryTestBase, self).setUp()
        self.system = IZBox(("address", 80))
        self.scenario = api_scenario(self.system, "izbox_handshake")
        self.scenario.start()
        self.addCleanup(self.scenario.end)

class QueryExecutionTest(QueryTestBase):

    def test_querying_length(self):
        all_filesystems = Filesystem.find(self.system)
        self.assertEquals(len(all_filesystems), 5)

class TypeBinderQueryTest(QueryTestBase):

    def test_get_too_many_items(self):
        with self.assertRaises(TooManyObjectsFound):
            self.system.objects.filesystems.get()

    def test_get_not_found(self):
        with self.assertRaises(ObjectNotFound):
            self.system.objects.filesystems.get(name="nonexisting")

    def test_choose_not_found(self):
        with self.assertRaises(ObjectNotFound):
            self.system.objects.filesystems.choose(name="nonexisting")


class QueryTest(TestCase):
    def setUp(self):
        super(QueryTest, self).setUp()
        self.system = IZBox(("address", 80))
        self.field = self.system.objects.filesystems.fields.id

    def test_querying_equal(self):
        for query in [
                Filesystem.find(self.system, id=2),
                Filesystem.find(self.system, Filesystem.fields.id==2),
        ]:
            self.assert_query_equals(query, "id=eq%3A2")

    def test_querying_ge(self):
        self.assert_query_equals(Filesystem.find(self.system, self.field >= "X"), "id=ge%3AX")

    def test_querying_le(self):
        self.assert_query_equals(Filesystem.find(self.system, self.field <= "X"), "id=le%3AX")

    def test_querying_gt(self):
        self.assert_query_equals(Filesystem.find(self.system, self.field > "X"), "id=gt%3AX")

    def test_querying_lt(self):
        self.assert_query_equals(Filesystem.find(self.system, self.field < "X"), "id=lt%3AX")

    def test_sorting(self):
        self.assert_query_equals(
            Filesystem.find(self.system).sort(-Filesystem.fields.quota), "sort=-quota_in_bytes")
        self.assert_query_equals(
            Filesystem.find(self.system).sort(+Filesystem.fields.quota), "sort=quota_in_bytes")
        self.assert_query_equals(
            Filesystem.find(self.system).sort(Filesystem.fields.quota), "sort=quota_in_bytes")

    def test_sorting_multiple(self):
        self.assert_query_equals(
            Filesystem.find(self.system).sort(-Filesystem.fields.quota, +Filesystem.fields.id), "sort=-quota_in_bytes%2Cid")

    def test_only_fields(self):
        # NOTE: uses api name!
        self.assert_query_equals(
            Filesystem.find(self.system).only_fields(["quota"]), "fields=quota_in_bytes")

    def assert_query_equals(self, q, expected):
        self.assertEquals(
            q.query, "/api/rest/filesystems?" + expected)
