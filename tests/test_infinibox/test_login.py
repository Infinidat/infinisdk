from requests import codes
import pytest
import logbook

from infinisdk.infinibox.infinibox import InfiniBox
from infinisdk.core.exceptions import APICommandFailed, CacheMiss
from infinibox_sysdefs.defs import latest


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

@pytest.mark.parametrize('user_role',list(latest.enums.users.roles))
def test_after_loging_operations(infinibox, user_role):
    _PASS = '123456'
    infinibox_simulator = infinibox.get_simulator()
    user = infinibox.users.create(role=str(user_role), password=_PASS)

    infinibox2 = InfiniBox(infinibox_simulator, auth=None)
    infinibox2.api.set_auth(user.get_name(), _PASS)
    with pytest.raises(CacheMiss):
        infinibox2.components.system_component.get_field('name', from_cache=True, fetch_if_not_cached=False)
    infinibox2.login()
    infinibox2.components.system_component.get_field('name', from_cache=True, fetch_if_not_cached=False)
