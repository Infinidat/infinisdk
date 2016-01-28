import re

import pytest

from ..conftest import no_op_context

from infinisdk import InfiniBox
from infinisdk.core.config import config
from infinisdk.core.exceptions import VersionNotSupported


def _login(s):
    return s.login()


def _get_volumes(s):
    return list(s.volumes)


@pytest.mark.parametrize('operator', [_login, _get_volumes])
def test_incompatible_version(incompatible_system, operator):
    with pytest.raises(VersionNotSupported):
        operator(incompatible_system)

    assert not incompatible_system.api._checked_version


@pytest.mark.parametrize('should_check_version', [True, False])
def test_ignore_version_check(incompatible_system, should_check_version):
    op_context = pytest.raises if should_check_version else no_op_context
    with op_context(VersionNotSupported):
        incompatible_system.api.get(
            '/api/rest/system', check_version=should_check_version)
    assert not incompatible_system.api._checked_version


def test_incompatible_version_stays_incompatible(incompatible_system):

    for retry in range(3):
        with pytest.raises(VersionNotSupported):
            incompatible_system.api.get('name')


@pytest.fixture(scope="module", autouse=True)
def restore_version_checks(request):

    prev = config.root.check_version_compatibility
    config.root.check_version_compatibility = True

    @request.addfinalizer
    def restore():
        config.root.check_version_compatibility = prev


@pytest.fixture
def incompatible_system(infinibox_simulator, incompatible_version):
    infinibox_simulator.set_version(incompatible_version)

    # simply initializing a system does not carry out any API commands
    user = infinibox_simulator.auth.get_current_user()
    auth = (user.get_username(), user.get_password())
    return InfiniBox(infinibox_simulator.get_floating_addresses()[0], auth=auth)


@pytest.fixture(params=[(1, 5), (1, 7)])
def incompatible_version(request, version_template):
    returned = version_template.format(major=request.param[0], minor=request.param[1])
    return returned


@pytest.fixture(params=[(1, 5), (1, 6), (2, 0)])
def major_minor(request):
    return request.param


@pytest.fixture(params=[
    '{major}.{minor}',
    '{major}.{minor}-bla',
    '{major}.{minor}.0',
    '{major}.{minor}.1',
    '{major}.{minor}.0.1',
    '{major}.{minor}.0.1-bla',
])
def version_template(request):
    return request.param


@pytest.fixture
def version_string(version_template, major_minor):
    major, minor = major_minor
    return version_template.format(major=major, minor=minor)
