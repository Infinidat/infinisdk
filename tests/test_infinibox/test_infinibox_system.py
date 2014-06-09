from infinisdk._compat import iteritems, string_types
from logbook import Logger

_logger = Logger(__name__)


def test_get_api_auth(infinibox):
    assert infinibox.get_api_auth() == ('infinidat', '123456')

def test_get_api_timeout(infinibox):
    assert infinibox.get_api_timeout() == 30

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
    ignore_types = ['volumes', 'users', 'emailrules']

    type_classes = [obj_type for obj_type in infinibox.OBJECT_TYPES
                    if obj_type.get_plural_name() not in ignore_types]

    _validate_single_metadata_support(volume)

    for type_class in type_classes:
        obj = type_class.create(infinibox)
        _validate_single_metadata_support(obj)

def test_infinibox_attributes(infinibox):
    assert infinibox.get_name().startswith('simulator')
    assert isinstance(infinibox.get_serial(), int)
    assert isinstance(infinibox.get_state(), string_types)
    assert isinstance(infinibox.get_version(), string_types)

def test_infinibox_system_type(infinibox):
    assert infinibox.is_simulator()
    assert not infinibox.is_mock()
