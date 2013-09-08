from unittest import TestCase
import os
import doctest

class DocTest(TestCase):
    def test_doctests(self):
        for path, _, filenames in os.walk(os.path.join(os.path.dirname(__file__), "..", "doc")):
            for filename in filenames:
                if not filename.endswith(".rst"):
                    continue
                filename = os.path.join(path, filename)
                result = doctest.testfile(filename, module_relative=False)
                if result.failed:
                    self.fail("{0}: {1} tests failed!".format(filename, result.failed))
