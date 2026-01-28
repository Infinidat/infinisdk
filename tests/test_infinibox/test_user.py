import pytest
from infinibox_sysdefs import latest as defs
import responses
from infinisdk.core import object_query
from infinisdk.core.exceptions import APICommandFailed
from tests.test_infinibox.mock_infinibox.mock_user import MOCK_USER_CREATION
from ..conftest import relevant_from_version
import http.client as httplib


def test_name(user):
    curr_name = user.get_name()
    new_name = 'other_user_name'
    user.update_name(new_name)

    assert curr_name.startswith('user_')
    assert curr_name != new_name
    assert user.get_name() == new_name


def test_get_administered_pools_no_pool(infinibox):
    assert infinibox.pools.get_administered_pools().to_list() == []


def test_get_administered_pools_multiple_pages(infinibox, user, forge):
    num_pools = 5
    for _ in range(num_pools):
        pool = infinibox.pools.create()
        pool.set_owners([user])
    page_size = num_pools - 1
    infinibox.get_simulator().api.set_default_page_size(page_size)
    forge.replace_with(object_query, '_DEFAULT_SYSTEM_PAGE_SIZE', page_size)
    assert len(list(infinibox.pools.get_administered_pools())) == num_pools


def test_get_administered_pools_with_pools(infinibox, user):
    pool = infinibox.pools.create()
    pool.set_owners([user])
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
    assert not user.is_in_system()


def test_password(user):
    with pytest.raises(AttributeError):
        user.get_password()
    user.update_password('some_password')


def test_email(user):
    orig_email = user.get_email()
    new_email = 'some@email.com'

    user.update_email(new_email)
    assert orig_email != new_email
    assert user.get_email() == new_email


def test_role(user):
    orig_role = user.get_role()
    new_role = defs.enums.users.roles.technician.get_name()

    user.update_role(new_role)
    assert orig_role != new_role
    assert user.get_role() == new_role


def test_get_owned_pools(infinibox, user):
    assert user.get_owned_pools() == []

    pool = infinibox.pools.create()
    pool.set_owners([user])

    pools = user.get_owned_pools()
    assert len(pools) == 1
    assert pools[0] == pool

    pool.set_owners([])
    assert user.get_owned_pools() == []


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


@relevant_from_version('2.2.8')
def test_enable_disable_user(user):
    assert user.is_enabled()
    user.disable()
    assert not user.is_enabled()
    user.enable()
    assert user.is_enabled()


def test_creation_with_invalid_password_policy(infinibox, infinibox_simulator_with_password_policy): # pylint: disable=unused-argument
    PASSWORD = 123456

    role = defs.enums.users.roles.technician.get_name()
    kwargs = {
        "role": role,
        "name": "some_user_name",
        "email": "fake@email.com",
        "password": PASSWORD,
    }

    with pytest.raises(APICommandFailed) as exception:
        infinibox.users.create(**kwargs)

    assert exception.value.status_code == httplib.BAD_REQUEST
    assert exception.value.error_code == "USER_PASSWORD_DOES_NOT_COMPLY_WITH_POLICY"
    assert (
        "User operation failed due to the password not complying with the policy"
        in str(exception.value)
    )


def test_creation_with_valid_password_policy(infinibox, infinibox_simulator_with_password_policy): # pylint: disable=unused-argument
    PASSWORD = "Aa1!aaa123456"

    role = defs.enums.users.roles.technician.get_name()
    kwargs = {
        "role": role,
        "name": "some_user_name",
        "email": "fake@email.com",
        "password": PASSWORD,
    }

    user = infinibox.users.create(**kwargs)

    assert user.get_name() == kwargs["name"]
    assert user.get_role() == kwargs["role"]
    assert user.get_email() == kwargs["email"]
    assert user in infinibox.users.get_all()
    user.delete()
    assert not user.is_in_system()


def test_mocked_user_creation(mocked_infinibox_api, mocked_infinibox):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/users?approved=true",
        json=MOCK_USER_CREATION,
    )
    user_data = {
        "role": "ADMIN",
        "name": "user1",
        "email": "user1@email.com",
        "password": "123456",
    }
    user = mocked_infinibox.users.create(**user_data)

    assert user.get_id() == 2
    assert user.get_name() == user_data["name"]
    assert user.get_role() == user_data["role"]
    assert user.get_email() == user_data["email"]