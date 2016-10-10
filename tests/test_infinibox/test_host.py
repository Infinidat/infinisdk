import pytest
from infinisdk._compat import iteritems
from infinisdk.core.config import config
from infinisdk.infinibox import InfiniBox

from ..conftest import relevant_from_version


def test_get_name(infinibox, host):
    assert host.get_name().startswith('host_')


def test_update_name(infinibox, host):
    curr_name = host.get_name()
    new_name = 'some_host_name'
    host.update_name(new_name)

    assert curr_name != new_name
    assert host.get_name() == new_name


def test_creation(infinibox, host, request):
    kwargs = {'name': 'some_host_name', }
    host = infinibox.hosts.create(**kwargs)
    request.addfinalizer(host.delete)

    for k, v in iteritems(kwargs):
        assert host._cache[k] == v

    assert host.get_cluster() is None


def test_get_cluster(infinibox, host, request):
    cluster = infinibox.host_clusters.create()
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


def test_get_host_by_initiator_address(infinibox, host, registered_port_address):
    assert infinibox.hosts.get_host_id_by_initiator_address(
        registered_port_address) == host.id
    assert infinibox.hosts.get_host_by_initiator_address(
        registered_port_address) == host


def test_get_host_by_initiator_address_no_address(infinibox, host):
    nonexisting_address = '00:01:02:03:04:05:06:07'
    assert infinibox.hosts.get_host_id_by_initiator_address(
        nonexisting_address) is None
    assert infinibox.hosts.get_host_by_initiator_address(
        nonexisting_address) is None


def test_has_registered_initiator_address(infinibox, host, registered_port_address):
    assert infinibox.hosts.has_registered_initiator_address(
        registered_port_address)
    assert not infinibox.hosts.has_registered_initiator_address(
        '00:01:02:03:04:05:06:08')


@relevant_from_version('3.0')
def test_get_host_initiator_without_auth(infinibox_simulator, host, registered_port_address, backup_config):
    config.root.check_version_compatibility = True
    system = InfiniBox(host.system.get_simulator())  # Unauthrozied system instance
    assert system.hosts.has_registered_initiator_address(registered_port_address)
    assert system.hosts.get_host_id_by_initiator_address(registered_port_address) == host.id
    assert system.hosts.get_host_by_initiator_address(registered_port_address).id == host.id


@pytest.fixture
def registered_port_address(host):
    returned = "00:01:02:03:04:05:06:07"
    host.add_fc_port(returned)
    return returned
