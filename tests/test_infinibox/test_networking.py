import pytest
import requests
from munch import Munch
from ..conftest import create_network_space, relevant_from_version, versioning_requiremnts
from infinisdk.core.exceptions import APICommandFailed
from infinisdk.core.api.special_values import OMIT


@relevant_from_version('2.0')
def test_disable_enable_network_interface(network_interface):
    assert network_interface.is_enabled()
    network_interface.disable()
    assert not network_interface.is_enabled()
    network_interface.enable()
    assert network_interface.is_enabled()

@pytest.mark.required_version(relevant_from='3.0', relevant_up_to='4.0')
def test_disable_enable_network_space_ip_without_type(network_space):
    ip_address = '127.0.0.1'
    assert network_space.get_ips() == []
    interface_id = network_space.get_interfaces()[0].get_id()
    network_space.add_ip_address(ip_address)
    assert network_space.get_ips() == [
        {'enabled': True, 'ip_address': ip_address, 'reserved': False, 'vlan_id': 1, 'interface_id': interface_id}]
    network_space.disable_ip_address(ip_address)
    assert network_space.get_ips() == [
        {'enabled': False, 'ip_address': ip_address, 'reserved': False, 'vlan_id': 1, 'interface_id': None}]
    network_space.enable_ip_address(ip_address)
    assert network_space.get_ips() == [
        {'enabled': True, 'ip_address': ip_address, 'reserved': False, 'vlan_id': 1, 'interface_id': interface_id}]
    network_space.disable_ip_address(ip_address)
    network_space.remove_ip_address(ip_address)
    assert network_space.get_ips() == []


@relevant_from_version('4.0')
def test_disable_enable_network_space_ip(network_space):
    ip_address = '127.0.0.1'
    assert network_space.get_ips() == []
    interface_id = network_space.get_interfaces()[0].get_id()
    network_space.add_ip_address(ip_address)
    assert network_space.get_ips() == [
        {'enabled': True, 'ip_address': ip_address, 'reserved': False, 'vlan_id': 1,
         'interface_id': interface_id, 'type': 'MANAGMENT'}]
    network_space.disable_ip_address(ip_address)
    assert network_space.get_ips() == [
        {'enabled': False, 'ip_address': ip_address, 'reserved': False, 'vlan_id': 1,
         'interface_id': None, 'type': 'MANAGMENT'}]
    network_space.enable_ip_address(ip_address)
    assert network_space.get_ips() == [
        {'enabled': True, 'ip_address': ip_address, 'reserved': False, 'vlan_id': 1,
         'interface_id': interface_id, 'type': 'MANAGMENT'}]
    network_space.disable_ip_address(ip_address)
    network_space.remove_ip_address(ip_address)
    assert network_space.get_ips() == []


@relevant_from_version('2.0')
def test_network_space_get_links_no_links(network_space):
    assert list(network_space.get_links()) == []


@relevant_from_version('2.0')
def test_network_space_get_links_with_links(infinibox, link):
    [ns] = infinibox.network_spaces
    assert [link] == list(ns.get_links())


@relevant_from_version('2.0')
def test_update_interface_list_of_network_space(infinibox):
    def create_interfaces(port_name):
        return [infinibox.network_interfaces.create(node_id=index, name=port_name, type='PORT')
                for index in range(1, 4)]
    network_space = create_network_space(infinibox, interfaces=create_interfaces('eth-data1'))
    origin_interfaces = network_space.get_interfaces()
    new_interfaces = create_interfaces('eth-data2')
    assert set(origin_interfaces) & set(new_interfaces) == set()
    network_space.update_interfaces(new_interfaces)
    assert network_space.get_interfaces() == new_interfaces


@relevant_from_version('2.0')
@pytest.mark.parametrize('network_config_type', [Munch, dict])
def test_network_configuration_type(infinibox, network_config_type):
    ip_address = '127.0.0.1'
    conf_for_creation = network_config_type(netmask=19, network='127.0.0.1', default_gateway='127.0.0.1')
    network_space = create_network_space(infinibox, network_config=conf_for_creation)
    network_config = network_space.get_network_config()
    assert network_config.default_gateway == network_config['default_gateway']
    network_space.add_ip_address(ip_address)
    ip_obj = network_space.get_ips()[0]
    assert ip_obj.ip_address == ip_obj['ip_address']


@versioning_requiremnts(relevant_from='2.0', relevant_up_to='3.0')
@pytest.mark.parametrize('service_value', [None, OMIT])
def test_create_network_space_with_no_service_until_3_0(infinibox, service_value):
    network_space = create_network_space(infinibox, service=service_value)
    assert network_space.get_service() is None


@relevant_from_version('3.0')
@pytest.mark.parametrize('service_value', [None, OMIT])
def test_create_network_space_with_no_service(infinibox, service_value):
    with pytest.raises(APICommandFailed) as exception:
        create_network_space(infinibox, service=service_value)
    assert exception.value.status_code == requests.codes.bad_request
