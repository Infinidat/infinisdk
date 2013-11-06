from ..utils import TestCase

class UserTest(TestCase):

    def test_has_users(self):
        self.assertTrue(self.system.users.find())
