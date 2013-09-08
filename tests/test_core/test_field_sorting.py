from ..utils import TestCase
from infinipy2.core import *
from urlobject import URLObject

class FieldSortingTest(TestCase):

    def setUp(self):
        super(FieldSortingTest, self).setUp()
        class TestObject(SystemObject):
            FIELDS = [
                Field("str_field", type=str),
                Field("int_field", type=str),
            ]
        self.cls = TestObject
        self.url = URLObject("http://a.com")

    def test_sorting_ascending(self):
        self.assertEquals(
            (-self.cls.fields.str_field).add_to_url(self.url),
            self.url.add_query_param("sort", "-str_field"))

    def test_sorting_ascending(self):
        self.assertEquals(
            (+self.cls.fields.str_field).add_to_url(self.url),
            self.url.add_query_param("sort", "str_field"))

    def test_sorting_multiple(self):
        url = self.url
        for sorting in [
                +self.cls.fields.str_field,
                -self.cls.fields.int_field
        ]:
            url = sorting.add_to_url(url)
        self.assertEquals(url,
            self.url.add_query_param("sort", "str_field,-int_field"))


