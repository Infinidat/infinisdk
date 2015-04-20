import pytest
from infinisdk._compat import iteritems, cmp, sorted
from infinisdk.core.exceptions import APICommandFailed


def test_get_nonexisting_metadata(volume):
    with pytest.raises(APICommandFailed):
        volume.get_metadata_value('key')


def test_get_nonexisting_metadata_default(volume):
    assert volume.get_metadata_value('key', 2) == 2
    value = object()
    assert volume.get_metadata_value('key', value) is value


def test_multiple_metadata_creation(volume):
    metadata_d = {'some_key':  'some_value',
                  'other_key': 'other_value',
                  'last_key':  'last_value'}
    volume.set_metadata_from_dict(metadata_d)
    assert volume.get_all_metadata() == metadata_d


def test_metadata_creation(infinibox, volume):
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


def test_get_all_metadata(infinibox, volume, pool):
    def _metadata_cmp(d_1, d_2):
        return cmp(d_1['object_id'], d_2['object_id']) or cmp(d_1['key'], d_2['key'])
    pool.set_metadata_from_dict({'b': 'c', 'd': 'd'})
    volume.set_metadata_from_dict({'a': 'a', 'b': 'b'})
    expected = [
        {'object_id': pool.id, 'key': 'b', 'value': 'c'},
        {'object_id': pool.id, 'key': 'd', 'value': 'd'},
        {'object_id': volume.id, 'key': 'a', 'value': 'a'},
        {'object_id': volume.id, 'key': 'b', 'value': 'b'},
        ]
    actual = list(infinibox.get_all_metadata())
    assert sorted(expected, cmp=_metadata_cmp) == sorted(actual, cmp=_metadata_cmp)
