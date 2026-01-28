import responses

from tests.test_infinibox.mock_infinibox.mock_s3credential import (
    MOCK_CREDENTIAL_CREATE,
    MOCK_CREDENTIAL_MODIFY,
)


def test_mocked_credential_creation(mocked_infinibox_api, mocked_infinibox, s3_user):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/s3_credentials?approved=true",
        json=MOCK_CREDENTIAL_CREATE,
    )
    credential_data = {
        "user": s3_user,
        "access_key": "AKIAEXAMPLE",
        "description": "Example",
    }

    credential = mocked_infinibox.s3_credentials.create(**credential_data)

    assert credential.get_id() == 41
    assert credential.get_access_key() == credential_data["access_key"]
    assert credential.get_description() == credential_data["description"]


def test_mocked_credential_update(mocked_infinibox_api, mocked_infinibox, s3_user):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/s3_credentials?approved=true",
        json=MOCK_CREDENTIAL_CREATE,
    )
    add_mock(
        method=responses.PUT,
        url="http://ibox3441:80/api/rest/s3_credentials/41?approved=true",
        json=MOCK_CREDENTIAL_MODIFY,
    )

    credential_data = {
        "user": s3_user,
        "access_key": "AKIAEXAMPLE",
        "description": "Example",
    }
    credential = mocked_infinibox.s3_credentials.create(**credential_data)
    credential.update_description("Example2")
    credential.update_status("DISABLED")

    assert credential.get_description() == "Example2"
    assert credential.get_status() == "DISABLED"
