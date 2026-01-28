import pytest


@pytest.fixture
def ldap_config(infinibox):
    infinibox.disable_caching()
    return infinibox.ldap_configs.define_open_ldap(name='ldap-conf', bind_username='Administrator', bind_password='passwd', servers=["AD2K3.local"]) 


def test_create_active_directory_ldap(infinibox):
    ldap_conf = infinibox.ldap_configs.define_active_directory(name='ldap-conf', domain_name='AD2K3.local', bind_username='Administrator', bind_password='passwd') 
    assert ldap_conf.get_domain_name() == "AD2K3.local"


def test_update_ldap_configs(ldap_config):
    update_dict = {"name": "my-new-name", "ldap_port": 12345}
    ldap_config.modify(**update_dict)
    assert ldap_config.get_name() == "my-new-name"
    assert ldap_config.get_ldap_port() == 12345
