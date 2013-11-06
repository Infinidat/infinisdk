from ..utils import TestCase

class IZBoxSystemTest(TestCase):

    def test_is_mock(self):
        self.assertFalse(self.system.is_mock())
