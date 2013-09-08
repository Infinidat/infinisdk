from ..utils import TestCase
from infinipy2.core import *

class TypeInfoTest(TestCase):

    def test_invalid_types(self):
        self.assert_not_valid(TypeInfo(str), 2)
        self.assert_not_valid(TypeInfo(bool), 2)
        self.assert_not_valid(TypeInfo(int), True)
        self.assert_not_valid(TypeInfo(str), True)

        self.assert_valid(TypeInfo(str), "hello")
        self.assert_valid(TypeInfo(str), "")
        self.assert_valid(TypeInfo(int), 10)
        self.assert_valid(TypeInfo(bool), True)

    def test_charsets(self):
        type_info = TypeInfo(str, charset="abc")
        self.assert_not_valid(type_info, "abcd")
        self.assert_not_valid(type_info, "def")
        self.assert_valid(type_info, "aaa")
        self.assert_valid(type_info, "")
        self.assert_valid(type_info, "abbbaacccb")

    def test_min_max(self):
        self.assert_not_valid(TypeInfo(int, min=120), 119)
        self.assert_not_valid(TypeInfo(int, max=120), 121)
        self.assert_not_valid(TypeInfo(int, min=120, max=140), 119)
        self.assert_valid(TypeInfo(int, min=120), 121)
        self.assert_valid(TypeInfo(int, max=120), 29)
        self.assert_valid(TypeInfo(int, min=120, max=140), 121)

    def test_min_max_length(self):
        self.assert_not_valid(TypeInfo(str, max_length=5), "hello!!!")
        self.assert_not_valid(TypeInfo(str, min_length=5), "hell")
        self.assert_not_valid(TypeInfo(str, min_length=5, max_length=6), "hello!!!")
        self.assert_not_valid(TypeInfo(str, min_length=5, max_length=6), "hell")
        self.assert_valid(TypeInfo(str, min_length=5, max_length=6), "hello")
        self.assert_valid(TypeInfo(str, min_length=5), "hello there")
        self.assert_valid(TypeInfo(str, max_length=5), "hey")


    def assert_not_valid(self, type_info, value):
        result, explanation = type_info.is_valid_value_explain(value)
        self.assertEquals(result, type_info.is_valid_value(value))

        if result:
            self.fail("{0}: Unexpectedly valid: {1!r}".format(type_info, value))
        self.assertIsInstance(explanation, str)

    def assert_valid(self, type_info, value):
        result, explanation = type_info.is_valid_value_explain(value)
        self.assertEquals(result, type_info.is_valid_value(value))

        if not result:
            self.fail("{0}: Unexpectedly invalid: {1!r} ({2})".format(type_info, value, explanation))

        self.assertIsNone(explanation)
