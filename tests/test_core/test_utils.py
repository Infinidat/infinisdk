import unittest
import doctest

from infinipy2.core import utils

class ObjectUtilsTest(unittest.TestCase):

    def test_add_comma_separated_query_param(self):
        self.assertEquals(utils.add_comma_separated_query_param("http://a.com/a/b/c", "sort", "a"),
                          'http://a.com/a/b/c?sort=a')
        self.assertEquals(utils.add_comma_separated_query_param("http://a.com/a/b/c?sort=a", "sort", "b"),
                          'http://a.com/a/b/c?sort=a%2Cb')

    def test_get_object_name_generator(self):
        self.assertTrue(utils.get_name_generator("someobj-{time}")().startswith("someobj-"))
        self.assertEquals(utils.get_name_generator("bla")(), "bla")
        generator = utils.get_name_generator("{ordinal}")
        name1 = generator()
        unrelated = utils.get_name_generator("bla{ordinal}")()
        name2 = generator()
        self.assertEquals(name1, "1")
        self.assertEquals(name2, "2")
