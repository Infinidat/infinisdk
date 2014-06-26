from requests import codes
import pytest

from infinisdk.core.exceptions import APICommandFailed


def test_login(infinibox):
    infinibox.login()

def test_invalid_login(infinibox):
    with infinibox.api.auth_context('a', 'b'):
        with pytest.raises(APICommandFailed) as caught:
            infinibox.login()

        assert caught.value.status_code in (codes.forbidden, codes.unauthorized)
