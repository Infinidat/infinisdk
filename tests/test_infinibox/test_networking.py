from infinisdk._compat import xrange

def test_disable_enable_network_interface(infinibox, network_interface, infinibox_simulator):
    sim_obj = infinibox_simulator.network_interfaces.get(network_interface.id)
    assert sim_obj.is_enabled()
    network_interface.disable()
    assert not sim_obj.is_enabled()
    network_interface.enable()
    assert sim_obj.is_enabled()


def test_disable_enable_network_space_ip(infinibox, network_space):
    ip_address = '127.0.0.1'
    assert network_space.get_field('ips') == []
    network_space.add_ip_address(ip_address)
    assert network_space.get_field('ips') == [{'enabled': True, 'ip_address': ip_address}]
    network_space.disable_ip_address(ip_address)
    assert network_space.get_field('ips') == [{'enabled': False, 'ip_address': ip_address}]
    network_space.enable_ip_address(ip_address)
    assert network_space.get_field('ips') == [{'enabled': True, 'ip_address': ip_address}]
    network_space.remove_ip_address(ip_address)
    assert network_space.get_field('ips') == []


def test_update_interface_list_of_network_space(infinibox, network_space):
    node_1 = infinibox.components.nodes.get(index=1)
    origin_interfaces = network_space.get_interfaces()
    new_interfaces = [infinibox.network_interfaces.create(node=node_1) for _ in xrange(3)]
    assert set(origin_interfaces) & set(new_interfaces) == set()
    network_space.update_interfaces(new_interfaces)
    assert network_space.get_interfaces() == new_interfaces
