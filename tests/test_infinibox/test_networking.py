import pytest
from munch import Munch
from ..conftest import create_network_space
from infinisdk._compat import xrange


def test_disable_enable_network_interface(infinibox, network_interface):
    assert network_interface.is_enabled()
    network_interface.disable()
    assert not network_interface.is_enabled()
    network_interface.enable()
    assert network_interface.is_enabled()


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


def test_update_interface_list_of_network_space(infinibox, network_space):
    node_1 = infinibox.components.nodes.get(index=1)
    origin_interfaces = network_space.get_interfaces()
    new_interfaces = [infinibox.network_interfaces.create(node=node_1) for _ in xrange(3)]
    assert set(origin_interfaces) & set(new_interfaces) == set()
    network_space.update_interfaces(new_interfaces)
    assert network_space.get_interfaces() == new_interfaces


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
