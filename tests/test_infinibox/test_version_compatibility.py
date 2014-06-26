import re

import pytest

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
    infinibox_simulator.set_version('{0}.{1}'.format(major, minor + 1))

    #simply initializing a system does not carry out any API commands
    return InfiniBox(infinibox_simulator.get_floating_addresses()[0])
