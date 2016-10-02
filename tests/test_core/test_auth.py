from requests import codes

import pytest
from infinisdk.core.exceptions import APICommandFailed


@pytest.mark.parametrize('params', [('other_username', 'other_password'), [('username', 'password')]])
def test_set_auth(infinibox, params):
    _assert_authorized(infinibox)

    infinibox.api.set_auth(*params, login=False)

    _assert_unauthorized(infinibox)


def test_get_auth_context(infinibox):
    _assert_authorized(infinibox)

    with pytest.raises(APICommandFailed):
        with infinibox.api.get_auth_context("other_username", "other_password"):
            assert False, 'shouldnt get here'

    _assert_authorized(infinibox)

def test_invalid_params(infinibox):
    for params in [
            [("a", "b"), "c"],
            ["a"],
    ]:
        with pytest.raises(TypeError):
            infinibox.api.set_auth(*params, login=False)

def _assert_authorized(infinibox):
    infinibox.api.get("volumes")


def _assert_unauthorized(infinibox):
    with pytest.raises(APICommandFailed) as caught:
        infinibox.api.get("volumes")
    assert caught.value.status_code == codes.unauthorized
