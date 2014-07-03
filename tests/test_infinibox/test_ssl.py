import pytest
from infinipy2 import InfiniBox


def test_ssl_works(ssl_infinibox):
    ssl_infinibox.login()

def test_ssl_verify(ssl_infinibox, ssl_certificate):
    if ssl_certificate is None:
        assert ssl_infinibox.api._session.verify == False
    else:
        assert ssl_infinibox.api._session.verify

def test_ssl_port(ssl_infinibox):
    for url in ssl_infinibox.api._urls:
        assert url.startswith("https://")
        assert url.netloc.port == 443

@pytest.fixture
def ssl_infinibox(request, infinibox_simulator, ssl_certificate):
    user = infinibox_simulator.auth.get_current_user()
    auth = (user.get_username(), user.get_password())
    returned = InfiniBox(
        infinibox_simulator.get_floating_addresses()[0], use_ssl=True,
        ssl_cert=ssl_certificate, auth=auth)
    assert returned.api._session.cert == ssl_certificate
    return returned

@pytest.fixture(params=[None, "some certificate"])
def ssl_certificate(request):
    return request.param
