from ..utils import TestCase

class IZBoxSystemTest(TestCase):

    def test_is_mock(self):
        self.assertFalse(self.system.is_mock())

    def test_is_virtual(self):
        self.assertFalse(self.system.is_virtual())

    def test_is_simulator(self):
        self.assertTrue(self.system.is_simulator())

    def test_get_serial(self):
        self.assertEqual(self.system.get_serial(), 25001)
