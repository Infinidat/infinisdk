import pytest


def create_idp(infinibox, name, issuer, sign_on_url):
    try:
        if not infinibox.compat.has_sso():
            pytest.skip("SSO not supported")
        return infinibox.sso_identity_providers.create(name=name, issuer=issuer, sign_on_url=sign_on_url)
    except AttributeError:
        pytest.skip("SSO not supported")


@pytest.fixture
def idp(infinibox):
    return create_idp(infinibox, "test-idp", "abc123", "http://www.test-idp.com")

# pylint: disable=unused-argument
def test_get_all_idps(infinibox, idp):
    idps = infinibox.sso_identity_providers.get_all().to_list() 
    assert len(idps) == 1
    assert idps[0].get_name() == "test-idp"


def test_get_single_idp(infinibox, idp):
    result_idp = infinibox.sso_identity_providers.get_by_id(idp.get_id())
    assert result_idp == idp


def test_update_idp(idp):
    idp.update_name("test2")
    assert idp.get_name() == "test2"


def test_delete_idp(infinibox, idp):
    idp.delete()
    idps = infinibox.sso_identity_providers.get_all().to_list()
    assert not idps
