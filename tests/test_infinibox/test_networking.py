import pytest
from munch import Munch
from ..conftest import create_network_space, new_to_version
from infinisdk._compat import xrange
from infinisdk.core.api.special_values import OMIT, RawValue


@new_to_version('2.0')
def test_disable_enable_network_interface(infinibox, network_interface):
    assert network_interface.is_enabled()
    network_interface.disable()
    assert not network_interface.is_enabled()
    network_interface.enable()
    assert network_interface.is_enabled()


@new_to_version('2.0')
def test_disable_enable_network_space_ip(infinibox, network_space):
    ip_address = '127.0.0.1'
    assert network_space.get_ips() == []
    network_space.add_ip_address(ip_address)
    assert network_space.get_ips() == [{'enabled': True, 'ip_address': ip_address}]
    network_space.disable_ip_address(ip_address)
    assert network_space.get_ips() == [{'enabled': False, 'ip_address': ip_address}]
    network_space.enable_ip_address(ip_address)
    assert network_space.get_ips() == [{'enabled': True, 'ip_address': ip_address}]
    network_space.remove_ip_address(ip_address)
    assert network_space.get_ips() == []


@new_to_version('2.0')
def test_update_interface_list_of_network_space(infinibox, network_space):
    node_1 = infinibox.components.nodes.get(index=1)
    origin_interfaces = network_space.get_interfaces()
    new_interfaces = [infinibox.network_interfaces.create(node=node_1) for _ in xrange(3)]
    assert set(origin_interfaces) & set(new_interfaces) == set()
    network_space.update_interfaces(new_interfaces)
    assert network_space.get_interfaces() == new_interfaces


@new_to_version('2.0')
@pytest.mark.parametrize('network_config_type', [Munch, dict])
def test_network_configuration_type(infinibox, network_config_type):
    ip_address = '127.0.0.1'
    conf_for_creation = network_config=network_config_type(netmask=19, network='127.0.0.1', default_gateway='127.0.0.1')
    network_space = create_network_space(infinibox, network_config=conf_for_creation)
    network_config = network_space.get_network_config()
    assert network_config.default_gateway == network_config['default_gateway']
    network_space.add_ip_address(ip_address)
    ip_obj = network_space.get_ips()[0]
    assert ip_obj.ip_address == ip_obj['ip_address']


@new_to_version('2.0')
@pytest.mark.parametrize('service_value', [None, OMIT])
def test_create_network_space_with_no_service(infinibox, service_value):
    network_space = create_network_space(infinibox, service=service_value)
    assert network_space.get_service() is None

@new_to_version('2.0')
def test_setting_service_to_special_value(infinibox):
    network_space = create_network_space(infinibox, service=RawValue('NAS_SERVICE'))
    network_space.update_service(RawValue(None))
    assert network_space.get_service() is None
