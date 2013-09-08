import operator
from infinipy2.core import *
from urlobject import URLObject
from infi.unittest import parameters
from ..utils import TestCase

class FieldFilterTest(TestCase):

    @parameters.toggle("use_api_name")
    def setUp(self, use_api_name):
        super(FieldFilterTest, self).setUp()

        kwargs = {"type": str}
        if use_api_name:
            kwargs.update(api_name="str_field_api_name")
            self.expected_api_name = "str_field_api_name"
        else:
            self.expected_api_name = "str_field"

        class TestObject(SystemObject):
            FIELDS = [
                Field("str_field", **kwargs),
            ]

        self.cls = TestObject

    def test_filter_eq(self):
        self._check_filter(self.cls.fields.str_field == "x", "eq")

    def _check_filter(self, filter, filter_name):
        self.assertIs(filter.field, self.cls.fields.str_field)

        self.assertEquals(
            str(filter.add_to_url(URLObject("http://a.com"))),
            "http://a.com?{0}={1}%3Ax".format(self.expected_api_name, filter_name))
