from requests import codes
import pytest
import logbook

from infinisdk.core.exceptions import APICommandFailed


def test_login(infinibox):
    infinibox.login()

def test_passwords_are_not_logged(infinibox):
    with logbook.TestHandler() as handler:
        password = '12345678'
        infinibox.api.set_auth('user', password)
        with pytest.raises(APICommandFailed) as caught:
            infinibox.login()

        assert password not in str(caught.value)
        assert password not in caught.value.response.sent_data

    for record in handler.records:
        assert password not in record.message


def test_invalid_login(infinibox):
    with infinibox.api.auth_context('a', 'b'):
        with pytest.raises(APICommandFailed) as caught:
            infinibox.login()

        assert caught.value.status_code in (codes.forbidden, codes.unauthorized)
