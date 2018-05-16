import pytest
from infinisdk import InfiniBox
from infinisdk.core import config


@pytest.mark.parametrize("use_username", [True, False])
@pytest.mark.parametrize("use_password", [True, False])
@pytest.mark.parametrize("specific_section", [True, False])
def test_auth_saving(infinibox_simulator, ini_path, use_username, use_password, specific_section):
    new_username = "some_user"
    new_password = "some_password"
    hostname = infinibox_simulator.get_floating_addresses()[0]
    with ini_path.open("w") as f:
        if specific_section:
            f.write("[infinibox:{}]\n".format(hostname))
        else:
            f.write("[infinibox]\n")

        if use_username:
            f.write("username={}\n".format(new_username))
            expected_username = new_username
        else:
            expected_username = "admin"
        if use_password:
            f.write("password={}".format(new_password))
            expected_password = new_password
        else:
            expected_password = ""
    s = InfiniBox(infinibox_simulator)

    if use_username or use_password:
        expected_auth = (expected_username, expected_password)
    else:
        expected_auth = None

    assert s.api.get_auth() == expected_auth

@pytest.fixture
def ini_path(request, tmpdir):
    assert hasattr(config, "_cached_ini_parser")
    config._cached_ini_parser = None  # pylint: disable=protected-access
    prev = config.config.root.ini_file_path
    ini_file_path = tmpdir.join("config.ini")
    config.config.root.ini_file_path = str(ini_file_path)

    @request.addfinalizer
    def cleanup():  # pylint: disable=unused-variable
        config.config.root.ini_file_path = prev
    return ini_file_path
