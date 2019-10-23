import functools
import pytest
from infinisdk.core.utils.python import cmp
from infinisdk.core import object_query
from infinisdk.core.exceptions import APICommandFailed

from ..conftest import relevant_from_version


def test_get_nonexisting_metadata(volume):
    with pytest.raises(APICommandFailed):
        volume.get_metadata_value('key')


def test_get_nonexisting_metadata_default(volume):
    assert volume.get_metadata_value('key', 2) == 2
    value = object()
    assert volume.get_metadata_value('key', value) is value

def test_metadata_paging(infinibox, volume, forge):
    page_size = 3
    infinibox.get_simulator().api.set_default_page_size(page_size)
    forge.replace_with(object_query, '_DEFAULT_SYSTEM_PAGE_SIZE', page_size)
    for i in range(page_size * 2):
        volume.set_metadata_from_dict({'key{}'.format(i): 'value{}'.format(i)})

    assert len(list(infinibox.get_all_metadata())) == page_size * 2


def test_multiple_metadata_creation(volume):
    metadata_d = {'some_key':  'some_value',
                  'other_key': 'other_value',
                  'last_key':  'last_value'}
    volume.set_metadata_from_dict(metadata_d)
    assert volume.get_all_metadata() == metadata_d


def test_metadata_creation(volume):
    metadata_d = {'some_key':  'some_value',
                  'other_key': 'other_value',
                  'last_key':  'last_value'}
    for k, v in metadata_d.items():
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


def _get_object_extras(system, obj):
    if system.compat.get_parsed_system_version() < '4.0.30':
        return {'object': None}
    return {'object': obj, 'object_type': obj.get_type_name()}


def _remove_id_keys(info_list):
    for info in info_list:
        info.pop('id')

def test_get_all_metadata(infinibox, volume, pool):
    def _metadata_cmp(d_1, d_2):
        return cmp(d_1['object_id'], d_2['object_id']) or cmp(d_1['key'], d_2['key'])
    _metadata_key = functools.cmp_to_key(_metadata_cmp)

    pool.set_metadata_from_dict({'b': 'c', 'd': 'd'})
    volume.set_metadata_from_dict({'a': 'a', 'b': 'b'})
    expected = [
        dict(object_id=pool.id, key='b', value='c', **_get_object_extras(infinibox, pool)),
        dict(object_id=pool.id, key='d', value='d', **_get_object_extras(infinibox, pool)),
        dict(object_id=volume.id, key='a', value='a', **_get_object_extras(infinibox, volume)),
        dict(object_id=volume.id, key='b', value='b', **_get_object_extras(infinibox, volume)),
        ]
    actual = list(infinibox.get_all_metadata())
    _remove_id_keys(actual)
    assert sorted(expected, key=_metadata_key) == sorted(actual, key=_metadata_key)

    expected = [
        dict(object_id=pool.id, key='b', value='c', **_get_object_extras(infinibox, pool)),
        dict(object_id=volume.id, key='b', value='b', **_get_object_extras(infinibox, volume)),
    ]
    actual = list(infinibox.get_all_metadata(key='b'))
    _remove_id_keys(actual)
    assert sorted(expected, key=_metadata_key) == sorted(actual, key=_metadata_key)


@relevant_from_version('3.0')
def test_set_system_metadata(infinibox):
    metadata = {'x': 'y'}
    infinibox.system_metadata.set_metadata_from_dict(metadata)
    assert infinibox.system_metadata.get_all_metadata() == metadata
