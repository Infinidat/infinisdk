from forge import Forge

import flux
import pytest
from infinisdk.core import extensions
from infinisdk.core.config import config
from infinisdk.infinibox import InfiniBox
from infinisdk.izbox import IZBox
from infinisim.infinibox import Infinibox as InfiniboxSimulator
from izsim import Simulator as IZBoxSimulator

import logbook.compat

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
def system(izbox, infinibox, system_type):
    if system_type == 'izbox':
        return izbox
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
    return InfiniBox(infinibox_simulator)


@pytest.fixture
def izbox_simulator(request):
    returned = IZBoxSimulator()
    returned.activate()
    request.addfinalizer(returned.deactivate)
    return returned


@pytest.fixture
def infinibox_simulator(request):
    returned = InfiniboxSimulator()
    returned.activate()
    request.addfinalizer(returned.deactivate)
    return returned

@pytest.fixture
def cluster(infinibox, request):
    returned = infinibox.clusters.create()
    request.addfinalizer(returned.delete)
    return returned

@pytest.fixture
def host(request, infinibox):
    returned = infinibox.hosts.create()
    request.addfinalizer(returned.delete)
    return returned

@pytest.fixture
def user(infinibox):
    return infinibox.users.create()


def create_volume(infinibox, **kwargs):
    if not kwargs.get('pool_id') and not kwargs.get('pool'):
        kwargs['pool_id'] = create_pool(infinibox).id
    vol = infinibox.volumes.create(**kwargs)
    return vol

def create_pool(infinibox, **kwargs):
    pool = infinibox.pools.create(**kwargs)
    return pool

@pytest.fixture
def pool(infinibox):
    return create_pool(infinibox)

@pytest.fixture
def volume(infinibox, pool):
    return create_volume(infinibox, pool_id=pool.id)

volume1 = volume2 = volume
