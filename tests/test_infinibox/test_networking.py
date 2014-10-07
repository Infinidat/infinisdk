import pytest


@pytest.skip('need infinisim network configuration support')
def test_disable_enable(infinibox, port_group):
    port_group.disable()
    assert not port_group.is_enabled()
    port_group.enable()
    assert port_group.is_enabled()


@pytest.fixture
def port_group(infinibox, node):
    return infinibox.portgroups.create(node=node.get_index())


@pytest.fixture(params=[0, 1, 2])
def node(infinibox, request):
    return list(infinibox.components.nodes)[request.param]
