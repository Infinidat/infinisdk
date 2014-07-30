import re

import pytest

from infinisdk.core.version_compatibility import All

from infinisdk import InfiniBox
from infinisdk.core.config import config
from infinisdk.core.exceptions import VersionNotSupported


def _get_name(s):
    return s.get_name()


def _get_volumes(s):
    return list(s.volumes)


@pytest.mark.parametrize('operator', [_get_name, _get_volumes])
def test_incompatible_version(incompatible_system, operator):
    with pytest.raises(VersionNotSupported):
        operator(incompatible_system)

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
def incompatible_system(infinibox_simulator):
    version = infinibox_simulator.get_version()
    match = re.match(r"^(\d+)\.(\d+).+", version)
    major = int(match.group(1))
    minor = int(match.group(2))
    infinibox_simulator.set_version('{0}.{1}'.format(major - 1, minor))

    # simply initializing a system does not carry out any API commands
    user = infinibox_simulator.auth.get_current_user()
    auth = (user.get_username(), user.get_password())
    return InfiniBox(infinibox_simulator.get_floating_addresses()[0], auth=auth)


def test_all_subversions_compatible(version_string, major_minor):
    major, minor = major_minor
    assert All(major, minor).matches(version_string)


def test_all_subversions_incompatible(version_string, major_minor):
    major, minor = major_minor
    assert not All(major, minor + 1).matches(version_string)


@pytest.fixture(params=[(1, 5), (1, 6), (2, 0)])
def major_minor(request):
    return request.param


@pytest.fixture(params=[
    '{major}.{minor}',
    '{major}.{minor}.0',
    '{major}.{minor}.1',
    '{major}.{minor}.0.1',
    '{major}.{minor}.0.1-bla',
])
def version_string(request, major_minor):
    major, minor = major_minor
    return request.param.format(major=major, minor=minor)
