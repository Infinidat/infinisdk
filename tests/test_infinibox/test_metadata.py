import pytest
from infinisdk._compat import iteritems
from infinisdk.core.exceptions import APICommandFailed


def test_get_nonexisting_metadata(infinibox, volume):

    with pytest.raises(APICommandFailed):
        volume.get_metadata_value('key')


def test_get_nonexisting_metadata_default(infinibox, volume):

    assert volume.get_metadata_value('key', 2) == 2
    value = object()
    assert volume.get_metadata_value('key', value) is value


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
