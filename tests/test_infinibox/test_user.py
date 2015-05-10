import pytest
import re
from infinibox_sysdefs import latest as defs
from ecosystem.mocks.mock_mailboxer import get_simulated_mail_server
from infinisdk.core import object_query
from ..conftest import new_to_version


def test_name(infinibox, user, user_name_field):
    curr_name = user.get_name()
    new_name = 'other_user_name'
    user.update_field(user_name_field, new_name)

    assert curr_name.startswith('user_')
    assert curr_name != new_name
    assert user.get_name() == new_name


@new_to_version('2.0')
def test_get_administered_pools_no_pool(infinibox, user):
    assert infinibox.pools.get_administered_pools().to_list() == []


@new_to_version('2.0')
def test_get_administered_pools_multiple_pages(infinibox, user, forge):
    num_pools = 5
    for i in range(num_pools):
        pool = infinibox.pools.create()
        pool.add_owner(user)
    page_size = num_pools - 1
    infinibox.get_simulator().api.set_default_page_size(page_size)
    forge.replace_with(object_query, '_DEFAULT_SYSTEM_PAGE_SIZE', page_size)
    assert len(list(infinibox.pools.get_administered_pools())) == num_pools


@new_to_version('2.0')
def test_get_administered_pools_with_pools(infinibox, user):
    pool = infinibox.pools.create()
    pool.add_owner(user)
    assert infinibox.pools.get_administered_pools().to_list() == [pool]


def test_creation_deletion(infinibox, user):
    role = defs.enums.users.roles.technician.get_name()
    kwargs = {"role": role,
              "name": "some_user_name",
              "email": "fake@email.com",
              "password": "some_password"}
    user = infinibox.users.create(**kwargs)

    assert user.get_name() == kwargs['name']
    assert user.get_role() == kwargs['role']
    assert user.get_email() == kwargs['email']
    assert user in infinibox.users.get_all()
    user.delete()
    assert (not user.is_in_system())


def test_password(infinibox, user):
    with pytest.raises(AttributeError):
        user.get_password()
    user.update_password('some_password')


def test_email(infinibox, user):
    orig_email = user.get_email()
    new_email = 'some@email.com'

    user.update_email(new_email)
    assert orig_email != new_email
    assert user.get_email() == new_email


def test_role(infinibox, user):
    orig_role = user.get_role()
    new_role = defs.enums.users.roles.technician.get_name()

    user.update_role(new_role)
    assert orig_role != new_role
    assert user.get_role() == new_role


def test_get_owned_pools(infinibox, user):
    assert user.get_owned_pools() == []

    pool = infinibox.pools.create()
    pool.add_owner(user)

    pools = user.get_owned_pools()
    assert len(pools) == 1
    assert pools[0] == pool

    pool.discard_owner(user)
    assert user.get_owned_pools() == []


@new_to_version('2.0')
def test_set_users(infinibox):
    user1 = infinibox.users.create(name='user1')
    user2 = infinibox.users.create(name='user2')
    assert user1.get_owned_pools() == []
    assert user2.get_owned_pools() == []

    pool = infinibox.pools.create()
    for owners in [[], [user1], [user2], [user1, user2]]:
        pool.set_owners(owners)
        assert pool.get_owners(from_cache=False) == owners
        for owner in owners:
            pools = owner.get_owned_pools()
            assert len(pools) == 1
            assert pools[0] == pool


def _get_token_from_mail(simulator, mail_address):
    msg = _get_last_mailboxer_msg(simulator, mail_address)
    return re.findall("token=(.*)\"", msg.content)[0]


def _get_last_mailboxer_msg(simulator, mail_address):
    msg = get_simulated_mail_server(simulator).get_messages(mail_address)
    return msg[0]


def test_reset_password(infinibox, infinibox_simulator, user):
    user_email = user.get_email()
    user.request_reset_password()
    token = _get_token_from_mail(infinibox_simulator, user_email)
    user.reset_password(token)
    msg = _get_last_mailboxer_msg(infinibox_simulator, user_email)
    assert 'successfully' in msg.content
