from contextlib import contextmanager

import flux
import logbook.compat
from forge import Forge
from packaging.version import parse as parse_version
from munch import Munch

import pytest

from ecosystem import SimulationContext
from infinisdk.core import extensions
from infinisdk.core.config import config
from infinisdk.infinibox import InfiniBox
from infinisdk.izbox import IZBox
from infinisim.infinibox import Infinibox as InfiniboxSimulator
from izsim import Simulator as IZBoxSimulator

new_to_version = lambda version: pytest.mark.required_version(from_version=version)


@pytest.fixture(scope="session", autouse=True)
def setup_logging(request):
    handler = logbook.compat.LoggingHandler()
    handler.push_application()

    _blacklisted = set(['infinisdk.core.api.api', 'infinisim.core.simulator'])

    logbook.NullHandler(filter=lambda r, h: r.channel in _blacklisted).push_application()


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

def validate_unittest_compatability_with_infinibox_version(system, **kwargs):
    from_version = kwargs.pop('from_version', None)
    until_version = kwargs.pop('until_version', None)
    assert not kwargs, "Version marker got unexpected kwargs: {0}".format(list(kwargs))
    sys_version = parse_version(system.get_version())

    if from_version is not None and parse_version(from_version) > sys_version:
        pytest.skip("System does not support this unittest (too old)")

    if until_version is not None and parse_version(until_version) > sys_version:
        pytest.skip("System does not support this unittest (too new)")

_DEFAULT_REQUIRED_VERSION = Munch(kwargs={})

@pytest.fixture
def infinibox(request, infinibox_simulator):
    user = infinibox_simulator.auth.get_current_user()
    infinibox = InfiniBox(infinibox_simulator, auth=(user.get_username(), user.get_password()))
    required_version_kwargs = getattr(request.function, 'required_version', _DEFAULT_REQUIRED_VERSION).kwargs
    validate_unittest_compatability_with_infinibox_version(infinibox, **required_version_kwargs)
    if int(infinibox.compat.get_version_major()) >= 2:
        infinibox.compat.set_feature_as_supported('nas')
    return infinibox


@pytest.fixture
def izbox_simulator(request):
    returned = IZBoxSimulator()
    returned.activate()
    request.addfinalizer(returned.deactivate)
    return returned


@pytest.fixture
def infinibox_simulator(request):
    returned = InfiniboxSimulator()
    returned.api.set_propagate_exceptions(True)
    returned.activate()
    request.addfinalizer(returned.deactivate)
    return returned

@pytest.fixture
def cluster(request, infinibox):
    return infinibox.host_clusters.create()

@pytest.fixture
def host(infinibox):
    return infinibox.hosts.create()


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

def create_export(infinibox, **kwargs):
    if not kwargs.get('filesystem_id') and not kwargs.get('filesystem'):
        kwargs['filesystem_id'] = create_filesystem(infinibox).id
    export = infinibox.exports.create(**kwargs)
    return export

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

@pytest.fixture
def export(infinibox, filesystem):
    return create_export(infinibox, filesystem=filesystem)

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

@pytest.fixture
def link(infinibox, secondary_infinibox, mocked_ecosystem):
    infinibox.login()  # to get the system name properly
    secondary_infinibox.login()

    for s in infinibox, secondary_infinibox:
        mocked_ecosystem.mocks.infinilab_client.get_mocked_infinilab().add_system(
            s.get_simulator())

    network_space = create_rmr_network_space(infinibox)
    remote_network_space = create_rmr_network_space(secondary_infinibox)
    returned = infinibox.links.create(
        name='link',
        local_replication_network_space=network_space,
        remote_host=remote_network_space.get_ips()[0].ip_address)
    return returned

def create_rmr_network_space(system):
    returned = system.network_spaces.create(
        name='rmr', interfaces=[i.id for i in system.network_interfaces],
        network_config={
            'default_gateway': '1.1.1.1',
            'netmask': '255.0.0.0',
            'network': '1.0.0.0',})
    assert not system.get_simulator().networking._allocated
    returned.add_ip_address(str(system.get_simulator().networking.allocate_ip_address('rmr')))
    return returned

@pytest.fixture
def mocked_ecosystem(request):
    context = SimulationContext(isolated_env=True)
    context.enter_mocked_context()
    request.addfinalizer(context.exit_mocked_context)
    return context


@pytest.fixture
def secondary_infinibox(request):
    returned = infinibox(request=request, infinibox_simulator=infinibox_simulator(request=request))
    unused = returned.get_simulator().hosts.create('unused_host') # make sure ids are not aligned
    return returned


@pytest.fixture(params=InfiniBox.OBJECT_TYPES)
def type_binder(request, infinibox):
    return infinibox.objects[request.param]
