from contextlib import contextmanager

import flux
import logbook.compat
from forge import Forge

import pytest
from infinisdk.core import extensions
from infinisdk.core.config import config
from infinisdk.infinibox import InfiniBox
from infinisdk.izbox import IZBox
from infinisdk_internal import disable as disable_infinisdk_internal
from infinisdk_internal import enable as enable_infinisdk_internal
from infinisim.infinibox import Infinibox as InfiniboxSimulator
from izsim import Simulator as IZBoxSimulator


@pytest.fixture(scope="session", autouse=True)
def setup_logging(request):
    handler = logbook.compat.LoggingHandler()
    handler.push_application()
    request.addfinalizer(handler.pop_application)

@pytest.fixture(scope="session", autouse=True)
def freeze_timeline(request):
    prev = flux.current_timeline.get_time_factor()
    @request.addfinalizer
    def restore():
        flux.current_timeline.set_time_factor(prev)
    flux.current_timeline.set_time_factor(0)

@pytest.fixture(scope="session", autouse=True)
def disable_version_checks():
    # speeds up the tests...
    config.root.check_version_compatibility = False

@pytest.fixture(autouse=True, scope='function')
def cleanup_extensions(request):
    @request.addfinalizer
    def cleanup():
        extensions.clear_all()


@pytest.fixture
def forge(request):
    returned = Forge()
    @request.addfinalizer
    def finalize():
        returned.restore_all_replacements()
        returned.verify()
    return returned

@pytest.fixture(params=['izbox', 'infinibox'])
def system_type(request):
    return request.param

@pytest.fixture
def system(infinibox):
    return infinibox

@pytest.fixture
def simulator(izbox_simulator, infinibox_simulator, system_type):
    if system_type == 'izbox':
        return izbox_simulator
    return infinibox_simulator

@pytest.fixture
def izbox(izbox_simulator):
    return IZBox(izbox_simulator)

@pytest.fixture
def infinibox(infinibox_simulator):
    user = infinibox_simulator.auth.get_current_user()
    return InfiniBox(infinibox_simulator, auth=(user.get_username(), user.get_password()))


@pytest.fixture
def izbox_simulator(request):
    returned = IZBoxSimulator()
    returned.activate()
    request.addfinalizer(returned.deactivate)
    return returned


@pytest.fixture
def infinibox_simulator(request):
    returned = InfiniboxSimulator(True)
    returned.activate()
    request.addfinalizer(returned.deactivate)
    return returned

@pytest.fixture
def cluster(request, infinibox):
    returned = infinibox.host_clusters.create()
    request.addfinalizer(_get_purge_callback(returned))
    return returned

@pytest.fixture
def host(request, infinibox):
    returned = infinibox.hosts.create()
    request.addfinalizer(_get_purge_callback(returned))
    return returned


def _get_purge_callback(obj):
    def cleanup():
        with enabling_infinisdk_internal():
            obj.purge()
    return cleanup

@contextmanager
def enabling_infinisdk_internal():
    assert not extensions.active
    enable_infinisdk_internal()
    try:
        yield
    finally:
        disable_infinisdk_internal()
        assert not extensions.active

@contextmanager
def no_op_context(*args):
    yield

@pytest.fixture(params=["host", "cluster"])
def mapping_object_type(request, infinibox):
    return request.param

@pytest.fixture
def mapping_object(host, cluster, mapping_object_type):
    if mapping_object_type == 'host':
        return host
    return cluster

@pytest.fixture
def user(infinibox):
    return infinibox.users.create()


def create_volume(infinibox, **kwargs):
    if not kwargs.get('pool_id') and not kwargs.get('pool'):
        kwargs['pool_id'] = create_pool(infinibox).id
    vol = infinibox.volumes.create(**kwargs)
    return vol

def create_filesystem(infinibox, **kwargs):
    if not kwargs.get('pool_id') and not kwargs.get('pool'):
        kwargs['pool_id'] = create_pool(infinibox).id
    fs = infinibox.filesystems.create(**kwargs)
    return fs

def create_pool(infinibox, **kwargs):
    pool = infinibox.pools.create(**kwargs)
    return pool

@pytest.fixture
def pool(infinibox):
    return create_pool(infinibox)

@pytest.fixture
def volume(infinibox, pool):
    return create_volume(infinibox, pool_id=pool.id)

def _map_to_cluster(infinibox, volume):
    host = infinibox.hosts.create()
    cluster = infinibox.host_clusters.create()
    cluster.add_host(host)
    cluster.map_volume(volume)

def _map_to_host(infinibox, volume):
    host = infinibox.hosts.create()
    host.map_volume(volume)

def _map_to_clustered_host(infinibox, volume):
    host = infinibox.hosts.create()
    cluster = infinibox.host_clusters.create()
    cluster.add_host(host)
    host.map_volume(volume)

@pytest.fixture(params=[_map_to_cluster, _map_to_host, _map_to_clustered_host])
def mapped_volume(infinibox, pool, request):
    returned = create_volume(infinibox, pool=pool)
    request.param(infinibox, returned)
    return returned

volume1 = volume2 = volume

@pytest.fixture
def filesystem(infinibox, pool):
    return create_filesystem(infinibox, pool_id=pool.id)

@pytest.fixture(params=['volume', 'filesystem'])
def data_entity_type(request):
    return request.param

@pytest.fixture
def data_entity(infinibox, volume, filesystem, data_entity_type):
    if data_entity_type == 'volume':
        return volume
    return filesystem


def create_network_interface(infinibox, **kwargs):
    if not kwargs.get('node') and not kwargs.get('node_id'):
        kwargs['node'] = infinibox.components.nodes.get(index=1)
    return infinibox.network_interfaces.create(**kwargs)


def create_network_space(infinibox, **kwargs):
    if not kwargs.get('network_config'):
        kwargs['network_config'] = {'netmask': 19, 'network': '127.0.0.1', 'default_gateway': '127.0.0.1'}
    if not kwargs.get('interfaces'):
        kwargs['interfaces'] = [create_network_interface(infinibox)]
    return infinibox.network_spaces.create(**kwargs)


@pytest.fixture
def network_interface(infinibox):
    return create_network_interface(infinibox)


@pytest.fixture
def network_space(infinibox, network_interface):
    return create_network_space(infinibox, interfaces=[network_interface])

@contextmanager
def disable_api_context(system):
    api = system.api
    system.api = None
    try:
        yield
    finally:
        system.api = api

@pytest.fixture
def backup_config(request):
    config.backup()
    request.addfinalizer(config.restore)
