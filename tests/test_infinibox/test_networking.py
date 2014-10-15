import pytest


def test_disable_enable(port_group):
    _disable_enable(port_group)


def test_disable_enable_ipdomain(infinibox, ipdomain):
    _disable_enable(ipdomain)


def _disable_enable(obj):
    obj.disable()
    assert not obj.is_enabled()
    obj.enable()
    assert obj.is_enabled()


@pytest.fixture
def port_group(infinibox, node):
    pytest.skip('need infinisim network configuration support')
    return infinibox.portgroups.create(node=node.get_index())

@pytest.fixture
def ipdomain(infinibox):
    pytest.skip('need infinisim network configuration support')
    return infinibox.ipdomains.create()


@pytest.fixture(params=[0, 1, 2])
def node(infinibox, request):
    return list(infinibox.components.nodes)[request.param]
