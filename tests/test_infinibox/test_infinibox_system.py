from ..utils import InfiniBoxTestCase


class InfiniBoxSystemTest(InfiniBoxTestCase):

    def test_get_api_auth(self):
        self.assertEqual(self.system.get_api_auth(), ('infinidat', '123456'))

    def test_get_api_timeout(self):
        self.assertEqual(self.system.get_api_timeout(), 30)
