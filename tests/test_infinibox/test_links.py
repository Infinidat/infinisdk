import pytest

from ..conftest import infinibox as _create_infinibox
from ..conftest import infinibox_simulator as _create_infinibox_simlator
from ecosystem.mocks import MockedContext


def test_link_creation(link):
    pass


def test_link_get_remote_link_id(infinibox, secondary_infinibox, link):
    remote_link_id = link.get_remote_link_id()
    remote_link = secondary_infinibox.links.get_by_id_lazy(remote_link_id)
    assert remote_link.is_in_system()


@pytest.fixture
def link(infinibox, secondary_infinibox, infinisdk_internal, mocked_ecosystem):
    infinibox.login()  # to get the system name properly
    secondary_infinibox.login()

    for s in infinibox, secondary_infinibox:
        mocked_ecosystem.mocks.infinilab_client.get_mocked_infinilab().add_system(
            s.get_simulator())

    network_space = infinibox.networking.ensure_default_network_space('rmr')
    remote_network_space = secondary_infinibox.networking.ensure_default_network_space(
        'rmr')
    return infinibox.links.create(
        name='link',
        local_replication_network_space=network_space,
        remote_host=remote_network_space.get_ips()[0].ip_address)


@pytest.fixture
def mocked_ecosystem(request):
    context = MockedContext(isolated_env=True)
    context.enter_mocked_context()
    request.addfinalizer(context.exit_mocked_context)
    return context


@pytest.fixture
def secondary_infinibox(request):
    returned = _create_infinibox(_create_infinibox_simlator(request=request))
    return returned
