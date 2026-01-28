from contextlib import contextmanager
from datetime import timedelta
from functools import wraps

import responses

import flux
import logbook.compat
import pytest
from ecosystem import SimulationContext
from forge import Forge
from infinisim.infinibox import Infinibox as InfiniboxSimulator
from munch import Munch
from sentinels import NOTHING

from infinisdk.core import extensions
from infinisdk.core.config import config
from infinisdk.infinibox import InfiniBox
from infinisdk.infinibox.compatibility import Compatibility
from tests.mocks.mock_conftest import MOCKED_FEAUTES
from tests.test_infinibox.mock_infinibox.mock_s3account import MOCK_ACCOUNT_CREATE, MOCK_S3_POOL_CREATION


# pylint: disable=redefined-outer-name
versioning_requiremnts = pytest.mark.required_version
relevant_from_version = lambda version: versioning_requiremnts(relevant_from=version)


def require_feature_flag(feature_name, feature_version=0):
    """
    A decorator to run tests only if the required
    feature flag is available
    """
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            infinibox = kwargs["infinibox"]
            compat = Compatibility(infinibox)
            existing_version = compat._get_feature_version(feature_name)  # pylint: disable=protected-access
            if (existing_version is not NOTHING) and (existing_version == feature_version):
                return func(*args, **kwargs)
            pytest.skip(f"Skipping test because feature {feature_name} with version {feature_version} is not supported")
        return wrapper
    return decorate


def pytest_addoption(parser):
    parser.addoption("--with-verbose-logs", action="store_true", default=False)


@pytest.fixture(scope="session", autouse=True)
def setup_logging(request):
    logbook.compat.redirect_logging()
    logbook.StderrHandler().push_application()

    if not request.config.getoption("--with-verbose-logs"):
        _blacklisted = set(['infinisdk.core.api.api', 'infinisim.core.simulator'])
        logbook.NullHandler(filter=lambda r, h: r.channel in _blacklisted).push_application()


@pytest.fixture(scope="session", autouse=True)
def freeze_timeline(request):
    prev = flux.current_timeline.get_time_factor()
    @request.addfinalizer
    def restore():  # pylint: disable=unused-variable
        flux.current_timeline.set_time_factor(prev)
    flux.current_timeline.set_time_factor(0)

@pytest.fixture(scope="session", autouse=True)
def disable_version_checks():
    # speeds up the tests...
    config.root.check_version_compatibility = False

@pytest.fixture(autouse=True, scope='function')
def cleanup_extensions(request):
    @request.addfinalizer
    def cleanup():  # pylint: disable=unused-variable
        extensions.clear_all()


@pytest.fixture
def forge(request):
    returned = Forge()
    @request.addfinalizer
    def finalize():  # pylint: disable=unused-variable
        returned.restore_all_replacements()
        returned.verify()
    return returned

@pytest.fixture
def system(infinibox):
    return infinibox

def validate_unittest_compatibility_with_infinibox_version(system, **kwargs):
    relevant_from = kwargs.pop('relevant_from', None)
    relevant_up_to = kwargs.pop('relevant_up_to', None)
    assert not kwargs, "Version marker got unexpected kwargs: {}".format(list(kwargs))
    sys_version = system.compat.normalize_version_string(system.get_version())

    if relevant_from is not None and sys_version < relevant_from:
        pytest.skip("System does not support this unittest (too old)")

    if relevant_up_to is not None and sys_version >= relevant_up_to:
        pytest.skip("System does not support this unittest (too new)")

_DEFAULT_REQUIRED_VERSION = Munch(kwargs={})


def create_infinibox_simulator(request):
    returned = InfiniboxSimulator()
    returned.features.native_smb.set_enabled(False)
    returned.config.mgmt['users.password_policy_enabled'] = False
    returned.api.set_propagate_exceptions(True)
    returned.activate()
    request.addfinalizer(returned.deactivate)
    return returned


def create_infinibox(request, simulator=None):
    if simulator is None:
        simulator = create_infinibox_simulator(request)

    user = simulator.auth.get_current_user()
    infinibox = InfiniBox(simulator, auth=(user.get_username(), user.get_password()))
    infinibox.login()
    required_version_kwargs = request.node.get_closest_marker('required_version', _DEFAULT_REQUIRED_VERSION).kwargs
    validate_unittest_compatibility_with_infinibox_version(infinibox, **required_version_kwargs)
    return infinibox


@pytest.fixture
def infinibox(request, infinibox_simulator):
    return create_infinibox(request, infinibox_simulator)

@pytest.fixture
def infinibox_simulator(request):
    return create_infinibox_simulator(request)

@pytest.fixture
def cluster(infinibox):
    return infinibox.host_clusters.create()

@pytest.fixture
def host(infinibox):
    return infinibox.hosts.create()


@contextmanager
def no_op_context(*args):  # pylint: disable=unused-argument
    yield


@pytest.fixture(params=["host", "cluster"])
def mapping_object_type(request):
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

def create_share(infinibox, **kwargs):
    if not kwargs.get('filesystem_id') and not kwargs.get('filesystem'):
        kwargs['filesystem_id'] = create_filesystem(infinibox).id
    share = infinibox.shares.create(**kwargs)
    return share

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

@pytest.fixture
def cg(pool):
    return pool.system.cons_groups.create(pool=pool)

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
def filesystem_windows(infinibox, pool):
    return create_filesystem(infinibox, pool_id=pool.id, security_style="WINDOWS")

@pytest.fixture
def export(infinibox, filesystem):
    return create_export(infinibox, filesystem=filesystem)

@pytest.fixture
def share(infinibox, filesystem):
    return create_share(infinibox, filesystem=filesystem)

@pytest.fixture(params=['volume', 'filesystem'])
def data_entity_type(request):
    return request.param


@pytest.fixture
def data_entity(volume, filesystem, data_entity_type):
    return volume if data_entity_type == 'volume' else filesystem


def create_network_interface(infinibox, **kwargs):
    if not kwargs.get('node') and not kwargs.get('node_id'):
        kwargs['node'] = infinibox.components.nodes.get(index=1)
    return infinibox.network_interfaces.create(**kwargs)


def create_network_space(infinibox, **kwargs):
    if not kwargs.get('network_config'):
        kwargs['network_config'] = {'netmask': 19, 'network': '127.0.0.1', 'default_gateway': '127.0.0.1'}
    if not kwargs.get('interfaces'):
        kwargs['interfaces'] = [create_network_interface(infinibox, node_id=index) for index in range(1, 4)]
    return infinibox.network_spaces.create(**kwargs)


@pytest.fixture
def network_interface(infinibox):
    return create_network_interface(infinibox)


@pytest.fixture
def network_space(infinibox, network_interface):
    interfaces = [create_network_interface(infinibox, node_id=index)
                  for index in range(1, 4) if index != network_interface.get_node().id]
    interfaces.append(network_interface)
    return create_network_space(infinibox, interfaces=interfaces)

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
    returned = create_network_space(infinibox=system, name='rmr', service="RMR_SERVICE",
        network_config={  # pylint: disable=bad-continuation
            'default_gateway': '1.1.1.1',
            'netmask': '255.0.0.0',
            'network': '1.0.0.0',})
    assert not system.get_simulator().networking._allocated  # pylint: disable=protected-access
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
    # pylint: disable=unused-variable
    returned = create_infinibox(request)
    unused = returned.get_simulator().hosts.create('unused_host') # make sure ids are not aligned
    return returned


@pytest.fixture(params=InfiniBox.OBJECT_TYPES)
def type_binder(request, infinibox):
    object_type = request.param
    if not object_type.is_supported(infinibox):
        pytest.skip('System does not support {}'.format(object_type.get_plural_name()))
    elif object_type.get_type_name() == 'fc_soft_target' and \
        infinibox.compat.get_version_major() < '3':
        pytest.skip('Soft targets are not supported by this infinisim version')
    elif object_type.get_type_name() == 's3_account':
        pytest.skip('S3 Accounts are not supported by Infinisim')
    elif object_type.get_type_name() == 's3_bucket':
        pytest.skip('S3 Buckets are not supported by Infinisim')
    elif object_type.get_type_name() == 's3_user':
        pytest.skip('S3 Users are not supported by Infinisim')
    elif object_type.get_type_name() == 's3_credential':
        pytest.skip('S3 Users are not supported by Infinisim')    
    return infinibox.objects[request.param]

@pytest.fixture
def volume_snapshot_and_schedule(infinibox, volume):
    policy1 = infinibox.snapshot_policies.create(name="policy1")
    schedule1 = policy1.schedules.create(name="test", interval=timedelta(seconds=3600), retention=timedelta(seconds=3600))
    policy1.assign_entity(entity=volume)
    flux.current_timeline.sleep(3600)  # virtual time of infinisim
    infinibox.api.post("snapshot_policies/trigger_snapshot_policies_service")
    for vol in infinibox.volumes.to_list():
        if vol.get_type() == "SNAPSHOT":
            return vol, schedule1

@pytest.fixture
def volume_from_cg_snapshot_and_schedule(infinibox, volume, cg):
    cg.add_member(volume)
    policy1 = infinibox.snapshot_policies.create(name="policy1")
    schedule1 = policy1.schedules.create(name="test", interval=timedelta(seconds=3600), retention=timedelta(seconds=3600))
    policy1.assign_entity(entity=cg)
    flux.current_timeline.sleep(3600)  # virtual time of infinisim
    infinibox.api.post("snapshot_policies/trigger_snapshot_policies_service")
    for cons_group in infinibox.cons_groups.to_list():
        if cons_group.get_type() == "SNAPSHOT":
            volume_snapshot = cons_group.get_members().to_list()[0]
            return volume_snapshot, schedule1


def create_internal_volumes(
        infinibox,
        volume = None, 
        internal_volume_type = 'snapshot',
        number_of_snapshots = 0
    ):
    if number_of_snapshots < 1:
        return
    
    if internal_volume_type.lower() != 'snapshot' or volume is None:
        volume = create_volume(infinibox)
        
    for _ in range(number_of_snapshots):
        volume_snapshot = volume.create_snapshot()
        volume_snapshot.promote_snapshot()

        # In order to change the internal volume type to be a master the parent volume should be deleted
        if internal_volume_type.lower() == 'master':
            volume.delete()
            volume = create_volume(infinibox)


def add_internal_volumes_to_system(
        number_of_internal_volumes_type_master = 0,
        number_of_internal_volumes_type_snapshot = 0
    ):
    """
    A decorator that adds internal volumes to the system
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'infinibox' in kwargs:
                infinibox = kwargs['infinibox']

                create_internal_volumes(
                    infinibox=infinibox,
                    internal_volume_type='snapshot',
                    number_of_snapshots=number_of_internal_volumes_type_snapshot
                )

                create_internal_volumes(
                    infinibox=infinibox,
                    internal_volume_type='master',
                    number_of_snapshots=number_of_internal_volumes_type_master
                )

            func(*args, **kwargs) 

        return wrapper
    return decorator

@pytest.fixture
def infinibox_simulator_with_password_policy(infinibox_simulator):
    returned = infinibox_simulator.config.mgmt["users.password_policy_enabled"] = True
    return returned

@pytest.fixture
def infinibox_with_network_space(request):
    returned = create_infinibox(request)
    create_network_space(returned)
    return returned

@pytest.fixture
def create_many_volumes(infinibox, pool):
    def _create_many_volumes(num_volumes=1):
        volumes = infinibox.volumes.create_many(count=num_volumes, pool=pool)
        return volumes
    return _create_many_volumes

@pytest.fixture
def create_many_filesystems(infinibox, pool):
    def _create_many_filesystems(num_filesystems=1):
        filesystems = infinibox.filesystems.create_many(count=num_filesystems, pool=pool)
        return filesystems
    return _create_many_filesystems

@pytest.fixture
def mocked_infinibox():
    """
    Fixture to provide an InfiniBox instance configured with mocked API responses.
    """
    base_url = "ibox3441"
    infinibox = InfiniBox(base_url, auth=("admin", "123456"))
    infinibox.login()
    return infinibox

@pytest.fixture
def mocked_infinibox_api():
    """Fixture to manage HTTP response mocks with dynamic overrides."""

    def add_mock(method, url, json, status=200, match=None, callback=None):
        """Allow tests to add their own mocks with optional matchers and callbacks."""
        if callback:
            mock.add_callback(method, url, callback=callback, match=match or [])
        else:
            mock.add(method, url, json=json, status=status, match=match or [])

    with responses.RequestsMock() as mock:
        # Common mocks
        mock.add(
            responses.GET,
            "http://ibox3441:80/api/rest/_features",
            json=MOCKED_FEAUTES,
            status=200,
        )

        mock.add(
            responses.POST,
            "http://ibox3441:80/api/rest/users/login",
            json={
                "result": {
                    "roles": ["ADMIN"],
                    "name": "admin",
                    "user_objects": [
                        {
                            "type": "Local",
                            "id": -2,
                            "role": "ADMIN",
                            "name": "admin",
                            "email": "dev.mgmt@infinidat.com",
                            "password_digest_version": 1,
                            "enabled": True,
                            "is_digest_sufficient": True,
                            "roles": ["ADMIN"],
                        }
                    ],
                }
            },
            status=200,
        )

        mock.add(
            responses.GET,
            "http://ibox3441:80/api/rest/system",
            json={
                "result": {
                    "name": "ibox3441",
                    "version": "8.6.0",
                }
            },
            status=200,
        )

        yield add_mock, mock

@pytest.fixture
def s3_pool(mocked_infinibox, mocked_infinibox_api):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/pools?approved=true",
        json=MOCK_S3_POOL_CREATION,
    )
    return create_pool(mocked_infinibox, type="S3")

@pytest.fixture
def s3_account(mocked_infinibox, mocked_infinibox_api, s3_pool):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/s3_accounts?approved=true",
        json=MOCK_ACCOUNT_CREATE,
    )
    account_data = {
        "name": "my_account",
        "pool": s3_pool,
        "email": "admin@abccomp.com",
        "location": "us-east-1",
    }
    return mocked_infinibox.s3_accounts.create(**account_data)

@pytest.fixture
def s3_user(mocked_infinibox, mocked_infinibox_api, s3_account):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/s3_users?approved=true",
        json=MOCK_ACCOUNT_CREATE,
    )
    user_data = {
        "name": "team-1",
        "account": s3_account,
        "root": True,
        "description": "Example",
    }
    return mocked_infinibox.s3_users.create(**user_data)
