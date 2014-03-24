from ..utils import TestCase
from infinipy2._compat import string_types

class IZBoxSystemTest(TestCase):

    def test_is_mock(self):
        self.assertFalse(self.system.is_mock())

    def test_is_virtual(self):
        self.assertFalse(self.system.is_virtual())

    def test_is_simulator(self):
        self.assertTrue(self.system.is_simulator())

    def test_get_serial(self):
        self.assertEqual(self.system.get_serial(), 25001)

    def test_get_state(self):
        self.assertEqual(self.system.get_state(), 'online')

    def test_get_model(self):
        self.assertEqual(self.system.get_model(), 'G3200')

    def test_get_version(self):
        self.assertTrue(isinstance(self.system.get_version(), string_types))
