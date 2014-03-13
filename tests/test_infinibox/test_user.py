from ecosystem.mocks.mock_mailboxer import get_simulated_mail_server
from tests.utils import InfiniBoxTestCase
import re


class UserTest(InfiniBoxTestCase):
    def setUp(self):
        super(UserTest, self).setUp()
        self.user = self.system.users.create()
        self.addCleanup(self.user.delete)

    def test_name(self):
        curr_name = self.user.get_name()
        new_name = 'other_user_name'
        self.user.update_name(new_name)

        self.assertTrue(curr_name.startswith('user_'))
        self.assertNotEqual(curr_name, new_name)
        self.assertEqual(self.user.get_name(), new_name)

    def test_creation(self):
        kwargs = {"role": "ReadOnly",
                  "name": "some_user_name",
                  "email": "fake@email.com",
                  "password": "some_password"}
        user = self.system.users.create(**kwargs)

        self.assertEqual(user.get_name(), kwargs['name'])
        self.assertEqual(user.get_role(), kwargs['role'])
        self.assertEqual(user.get_email(), kwargs['email'])
        self.assertIn(user, self.system.users.get_all())
        user.delete()
        self.assertFalse(user.is_in_system())

    def test_password(self):
        with self.assertRaises(AttributeError):
            self.user.get_password()
        self.user.update_password('some_password')

    def test_email(self):
        orig_email = self.user.get_email()
        new_email = 'some@email.com'

        self.user.update_email(new_email)
        self.assertNotEqual(orig_email, new_email)
        self.assertEqual(self.user.get_email(), new_email)

    def test_role(self):
        orig_role = self.user.get_role()
        new_role = 'ReadOnly'

        self.user.update_role(new_role)
        self.assertNotEqual(orig_role, new_role)
        self.assertEqual(self.user.get_role(), new_role)

    def test_get_pools(self):
        user = self.system.users.create(role='PoolAdmin')
        self.assertEquals(user.get_pools(), [])

        pool = self.system.pools.create()
        pool.add_owner(user)

        pools = user.get_pools()
        self.assertEquals(len(pools), 1)
        self.assertEquals(pools[0], pool)

        pool.discard_owner(user)
        self.assertEquals(user.get_pools(), [])

    def _get_token_from_mail(self, mail_address):
        msg = self._get_last_mailboxer_msg(mail_address)
        return re.findall("token=(.*)\"", msg.content)[0]

    def _get_last_mailboxer_msg(self, mail_address):
        msg = get_simulated_mail_server(self.simulator).get_messages(mail_address)
        return msg[0]

    def test_reset_password(self):
        user_email = self.user.get_email()
        self.user.request_reset_password()
        token = self._get_token_from_mail(user_email)
        self.user.reset_password(token)
        msg = self._get_last_mailboxer_msg(user_email)
        self.assertTrue('successfully' in msg.content)
