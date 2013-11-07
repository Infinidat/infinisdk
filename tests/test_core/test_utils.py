import unittest
import doctest

from infinipy2.core import utils

class ObjectUtilsTest(unittest.TestCase):

    def test_add_comma_separated_query_param(self):
        self.assertEquals(utils.add_comma_separated_query_param("http://a.com/a/b/c", "sort", "a"),
                          'http://a.com/a/b/c?sort=a')
        self.assertEquals(utils.add_comma_separated_query_param("http://a.com/a/b/c?sort=a", "sort", "b"),
                          'http://a.com/a/b/c?sort=a%2Cb')
