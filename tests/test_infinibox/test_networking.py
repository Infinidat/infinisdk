import pytest


def test_disable_enable(network_interface):
    _disable_enable(network_interface)


def test_disable_enable_network_space(infinibox, network_space):
    _disable_enable(network_space)


def test_disable_enable_network_space_ip(infinibox, network_space):
    ips = network_space.get_field('ips')
    network_space.disable_ip_address(ips[0])
    network_space.enable_ip_address(ips[0])


def _disable_enable(obj):
    obj.disable()
    assert not obj.is_enabled()
    obj.enable()
    assert obj.is_enabled()


@pytest.fixture
def network_interface(infinibox, node):
    pytest.skip('need infinisim network configuration support')
    return infinibox.network_interfaces.create(node=node.get_index())


@pytest.fixture
def network_space(infinibox):
    pytest.skip('need infinisim network configuration support')
    return infinibox.network_spaces.create()


@pytest.fixture(params=[0, 1, 2])
def node(infinibox, request):
    return list(infinibox.components.nodes)[request.param]
