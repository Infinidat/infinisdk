import responses

from tests.test_infinibox.mock_infinibox.mock_s3account import MOCK_ACCOUNT_CREATE


def test_mocked_account_creation(mocked_infinibox_api, mocked_infinibox, s3_pool):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/s3_accounts?approved=true",
        json=MOCK_ACCOUNT_CREATE,
    )
    account_data = {
        "name": "my_account",
        "pool": s3_pool,
        "email": "admin@abccomp.com",
        "location": "us-east-1",
    }
    account = mocked_infinibox.s3_accounts.create(**account_data)

    assert account.get_id() == 11111
    assert account.get_name() == account_data["name"]
    assert account.get_email() == account_data["email"]
    assert account.get_pool_name() == "pool-1"
