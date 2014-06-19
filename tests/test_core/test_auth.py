from requests import codes

import pytest
from infinipy2.core.exceptions import APICommandFailed


@pytest.mark.parametrize('params', [('other_username', 'other_password'), [('username', 'password')]])
def test_set_auth(infinibox, params):
    _assert_authorized(infinibox)

    infinibox.api.set_auth(*params)

    _assert_unauthorized(infinibox)


def test_auth_context(infinibox):
    _assert_authorized(infinibox)

    with infinibox.api.auth_context("other_username", "other_password"):
        _assert_unauthorized(infinibox)

    _assert_authorized(infinibox)

def test_invalid_params(infinibox):
    for params in [
            [("a", "b"), "c"],
            ["a"],
            ]:
        with pytest.raises(TypeError):
            infinibox.api.set_auth(*params)

def _assert_authorized(infinibox):
    infinibox.api.get("volumes")


def _assert_unauthorized(infinibox):
    with pytest.raises(APICommandFailed) as caught:
        infinibox.api.get("volumes")
    assert caught.value.status_code == codes.unauthorized
