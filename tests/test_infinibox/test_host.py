import pytest
from infinisdk._compat import iteritems


def test_get_name(infinibox, host):
    assert host.get_name().startswith('host_')

def test_update_name(infinibox, host):
    curr_name = host.get_name()
    new_name = 'some_host_name'
    host.update_name(new_name)

    assert curr_name != new_name
    assert host.get_name() == new_name

def test_creation(infinibox, host, request):
    kwargs = {'name': 'some_host_name',}
    host = infinibox.hosts.create(**kwargs)
    request.addfinalizer(host.delete)

    for k, v in iteritems(kwargs):
        assert host._cache[k] == v

    assert host.get_cluster() is None

def test_get_cluster(infinibox, host, request):
    cluster = infinibox.clusters.create()
    request.addfinalizer(cluster.delete)
    cluster.add_host(host)
    assert host.get_cluster() == cluster

def test_fc_port_operations(infinibox, host):
    address1 = "00:01:02:03:04:05:06:07"
    address2 = "07:06:05:04:03:02:01:00"

    assert host.get_fc_ports() == []
    host.add_fc_port(address1)
    host.add_fc_port(address2)

    assert sorted([address1, address2]) == sorted(host.get_fc_ports())

    host.remove_fc_port(address1)
    assert [address2] == host.get_fc_ports()

    host.remove_fc_port(address2)
    assert [] == host.get_fc_ports()

