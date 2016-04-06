from capacity import Capacity
from logbook import Logger
from sentinels import NOTHING
from waiting import wait

import pytest

from ..conftest import disable_api_context, new_to_version
from infinibox_sysdefs.defs import latest as defs
from infinisdk._compat import iteritems, string_types
from infinisdk.core.exceptions import (APITransportFailure,
                                       SystemNotFoundException)
from infinisdk.infinibox import InfiniBox
from infinisdk.infinibox.system_object import InfiniBoxObject

_logger = Logger(__name__)


def test_non_exist_system():
    infinibox = InfiniBox('fake_system')
    with pytest.raises(SystemNotFoundException) as caught:
        infinibox.get_version()
        assert caught.exception.address == 'fake_system'


def test_api_transport_error(infinibox):
    infinibox.api.post('system/operational_state/shutdown')
    wait(infinibox.components.system_component.is_down)
    url = infinibox.components.system_component.get_this_url_path()
    with pytest.raises(APITransportFailure) as e:
        infinibox.api.get(url)
    transport_repr = repr(e.value)
    assert url in transport_repr
    assert 'get' in transport_repr
    assert infinibox.get_name() in transport_repr


def test_get_api_auth(infinibox):
    assert infinibox.get_api_auth() == ('infinidat', '123456')


def test_get_api_timeout(infinibox):
    assert infinibox.get_api_timeout() == 30
    new_timeout = 50
    infinibox.api.set_request_default_timeout(new_timeout)
    assert infinibox.api.get_request_default_timeout() == new_timeout
    assert infinibox.get_api_timeout() == new_timeout

def test_change_request_default_timeout_context(infinibox):
    orig_timeout = infinibox.api.get_request_default_timeout()
    some_timeout = 100
    assert orig_timeout != some_timeout
    with infinibox.api.change_request_default_timeout_context(some_timeout):
        assert infinibox.api.get_request_default_timeout() == some_timeout
    assert infinibox.api.get_request_default_timeout() == orig_timeout

def test_get_simulator(infinibox, infinibox_simulator):
    assert infinibox.get_simulator() is infinibox_simulator


def test_multiple_metadata_creation(infinibox, volume):
    metadata_d = {'some_key':  'some_value',
                  'other_key': 'other_value',
                  'last_key':  'last_value'}
    for k, v in iteritems(metadata_d):
        volume.set_metadata(k, v)

    all_metadata = volume.get_all_metadata()
    assert len(all_metadata) == len(metadata_d)
    assert all_metadata == metadata_d

    metadata_val = volume.get_metadata_value('other_key')
    assert metadata_val == 'other_value'

    volume.unset_metadata('some_key')
    all_metadata = volume.get_all_metadata()
    assert len(all_metadata) == (len(metadata_d) - 1)
    metadata_d.pop('some_key')
    assert all_metadata == metadata_d

    volume.clear_metadata()
    assert len(volume.get_all_metadata()) == 0


def _validate_single_metadata_support(obj):
    _logger.debug("Validating {0}'s metadata support", type(obj).__name__)
    key, value = 'some_key', 'some_value'
    obj.set_metadata(key, value)
    all_metadata = obj.get_all_metadata()

    assert len(all_metadata) == 1
    assert all_metadata == {key: value}
    assert obj.get_metadata_value(key) == value
    obj.unset_metadata(key)
    assert len(obj.get_all_metadata()) == 0


def test_get_collections_names(infinibox):
    collections_names = infinibox.get_collections_names()
    assert len(collections_names) == len(infinibox.OBJECT_TYPES)
    assert 'volumes' in collections_names


def test_single_metadata_creation_on_all_infinibox_objects(infinibox, volume):
    def should_ignore_type(obj_type):
        if not issubclass(obj_type, InfiniBoxObject):
            return True
        for field in obj_type.fields:
            if field.creation_parameter and field.generate_default() is NOTHING:
                return True
        return False

    type_classes = [
        obj_type for obj_type in infinibox.OBJECT_TYPES if not should_ignore_type(obj_type)]
    _validate_single_metadata_support(volume)

    for type_class in type_classes:
        obj = type_class.create(infinibox)
        _validate_single_metadata_support(obj)


def test_infinibox_attributes(infinibox):
    assert isinstance(repr(infinibox), string_types)
    assert isinstance(infinibox.get_serial(), int)
    assert isinstance(infinibox.get_state(), string_types)
    assert isinstance(infinibox.get_version(), string_types)
    assert isinstance(infinibox.get_revision(), string_types)


def test_infinibox_system_type(infinibox):
    assert infinibox.is_simulator()
    assert not infinibox.is_mock()


def test_get_name(infinibox):
    simulator_host_name = infinibox.get_simulator().get_hostname()
    auth = infinibox.api.get_auth()
    infinibox = InfiniBox(infinibox.get_simulator())
    # NO LOGIN!

    with disable_api_context(infinibox):
        assert infinibox.get_name() == simulator_host_name

    infinibox.components.system_component.update_field_cache(
        {'name': 'fake_name'})
    assert infinibox.get_name() == 'fake_name'
    infinibox.api.set_auth(*auth, login=True)
    infinibox.components.system_component.refresh()
    assert infinibox.get_name().startswith('simulator-')


@pytest.mark.parametrize('from_cache', [True, False])
@pytest.mark.parametrize('invalidate_cache', [True, False])
def test_get_field_raw_value(volume, from_cache, invalidate_cache):
    if invalidate_cache:
        volume.refresh('size')
    assert isinstance(volume.get_size(from_cache=from_cache), Capacity)
    if invalidate_cache:
        volume.refresh('size')
    assert isinstance(
        volume.get_size(from_cache=from_cache, raw_value=False), Capacity)
    if invalidate_cache:
        volume.refresh('size')
    assert isinstance(
        volume.get_size(from_cache=from_cache, raw_value=True), int)


@new_to_version('2.0')
def test_current_user_proxy(infinibox):
    assert isinstance(infinibox.current_user.get_owned_pools().to_list(), list)


def test_current_user_roles(infinibox):
    infinidat_roles = infinibox.current_user.get_roles()
    assert infinidat_roles == [defs.enums.users.roles.infinidat.get_name()]

def test_infinibox_hashing(infinibox_simulator):
    user = infinibox_simulator.auth.get_current_user()
    infinibox1 = InfiniBox(infinibox_simulator, auth=(user.get_username(), user.get_password()))
    infinibox2 = InfiniBox(infinibox_simulator, auth=(user.get_username(), user.get_password()))
    assert infinibox1 == infinibox2
    assert (not infinibox1 != infinibox2)
    assert hash(infinibox1) == hash(infinibox2)


def test_is_eq_no_api(infinibox, secondary_infinibox):
    infinibox.api = None
    secondary_infinibox.api = None
    assert(infinibox != secondary_infinibox)
