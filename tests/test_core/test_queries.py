import operator
from infinipy2.core import *
from infinipy2.core.exceptions import ObjectNotFound, TooManyObjectsFound
from infinipy2.izbox import IZBox
from infinipy2.izbox.filesystem import Filesystem
from ..utils import TestCase
from urlobject import URLObject


class QueryExecutionTest(TestCase):

    def test_querying_length(self):
        self.assertEquals(len(Filesystem.find(self.system)), 0)
        self.simulator.create_filesystem("fs1")
        self.assertEquals(len(Filesystem.find(self.system)), 1)

class TypeBinderQueryTest(TestCase):

    def test_get_too_many_items(self):
        for i in range(2):
            self.simulator.create_filesystem("fs{}".format(i))
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

    def test_unknown_fields(self):
        self.assert_query_equals(Filesystem.find(self.system, unknown_field=2), "unknown_field=eq%3A2")

    def test_querying_ne(self):
        self.assert_query_equals(Filesystem.find(self.system, self.field != "X"), "id=ne%3AX")

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
            Filesystem.find(self.system).only_fields(["quota"]), "fields=id%2Cquota_in_bytes")

    def test_pagination(self):
        self.assert_query_equals(
            Filesystem.find(self.system).page(5).page_size(100), None) # pages are only added at query

    def assert_query_equals(self, q, expected):
        if expected is not None:
            expected = "?{}".format(expected)
        else:
            expected = ""
        self.assertEquals(
            q.query, "/api/rest/filesystems" + expected)


class PagedQueryTest(TestCase):

    def test_paged_query_traversal(self):
        """
        Makes sure that traversing a paged query only returns the requested page
        """
        page_size = 10
        result = self.system.components.find().page(5).page_size(page_size)
        self.assertEquals(len(result), page_size)
