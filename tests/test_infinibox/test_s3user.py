import responses

from tests.test_infinibox.mock_infinibox.mock_s3user import (
    MOCK_USER_CREATE,
    MOCK_USER_DISABLE_ROOT,
)


def test_mocked_user_creation(mocked_infinibox_api, mocked_infinibox, s3_account):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/s3_users?approved=true",
        json=MOCK_USER_CREATE,
    )

    user_data = {
        "name": "team-1",
        "account": s3_account,
        "root": True,
        "description": "Example",
    }

    user = mocked_infinibox.s3_users.create(**user_data)

    assert user.get_id() == 23
    assert user.get_name() == user_data["name"]
    assert user.is_root() == user_data["root"]
    assert user.get_description() == user_data["description"]


def test_mocked_account_update_root(mocked_infinibox_api, mocked_infinibox, s3_account):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/s3_users?approved=true",
        json=MOCK_USER_CREATE,
    )
    add_mock(
        method=responses.PUT,
        url="http://ibox3441:80/api/rest/s3_users/23?approved=true",
        json=MOCK_USER_DISABLE_ROOT,
    )

    user_data = {
        "name": "team-1",
        "account": s3_account,
        "root": True,
        "description": "Example",
    }

    user = mocked_infinibox.s3_users.create(**user_data)
    user.disable_root()
    assert user.is_root() == False
