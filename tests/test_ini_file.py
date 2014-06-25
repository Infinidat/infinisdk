import pytest
from infinisdk import InfiniBox
from infinisdk.core import config


@pytest.mark.parametrize("use_username", [True, False])
@pytest.mark.parametrize("use_password", [True, False])
def test_auth_saving(infinibox_simulator, ini_path, use_username, use_password):
    new_username = "some_user"
    new_password = "some_password"
    with ini_path.open("w") as f:
        f.write("[infinibox]\n")
        if use_username:
            f.write("username={0}\n".format(new_username))
            expected_username = new_username
        else:
            expected_username = "infinidat"
        if use_password:
            f.write("password={0}".format(new_password))
            expected_password = new_password
        else:
            expected_password = "123456"
    s = InfiniBox(infinibox_simulator)
    assert s.api.get_auth() == (expected_username, expected_password)

@pytest.fixture
def ini_path(request, tmpdir):
    assert hasattr(config, "_cached_ini_parser")
    config._cached_ini_parser = None
    prev = config.config.root.ini_file_path
    ini_file_path = tmpdir.join("config.ini")
    config.config.root.ini_file_path = str(ini_file_path)

    @request.addfinalizer
    def cleanup():
        config.config.root.ini_file_path = prev
    return ini_file_path
