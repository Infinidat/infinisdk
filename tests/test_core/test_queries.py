import pytest
from infinisdk.core import *
from infinisdk.core.exceptions import ObjectNotFound, TooManyObjectsFound
from infinisdk.izbox.filesystem import Filesystem


def test_querying_length(izbox, izbox_simulator):
    assert len(Filesystem.find(izbox)) == 0
    izbox_simulator.create_filesystem("fs1")
    assert len(Filesystem.find(izbox)) == 1


def test_get_too_many_items(izbox, izbox_simulator):
    for i in range(2):
        izbox_simulator.create_filesystem("fs{0}".format(i))
    with pytest.raises(TooManyObjectsFound):
        izbox.objects.filesystems.get()


def test_get_not_found(izbox):
    with pytest.raises(ObjectNotFound):
        izbox.objects.filesystems.get(name="nonexisting")


def test_choose_not_found(izbox):
    with pytest.raises(ObjectNotFound):
        izbox.objects.filesystems.choose(name="nonexisting")


@pytest.fixture
def field(izbox):
    return izbox.objects.filesystems.fields.id


def test_querying_equal(izbox, field):
    for query in [
            Filesystem.find(izbox, id=2),
            Filesystem.find(izbox, Filesystem.fields.id == 2),
    ]:
        assert_query_equals(query, "id=eq%3A2")


def test_unknown_fields(izbox, field):
    assert_query_equals(Filesystem.find(izbox, unknown_field=2),
                        "unknown_field=eq%3A2")


def test_querying_ne(izbox, field):
    assert_query_equals(Filesystem.find(izbox, field != "X"), "id=ne%3AX")


def test_querying_ge(izbox, field):
    assert_query_equals(Filesystem.find(izbox, field >= "X"), "id=ge%3AX")


def test_querying_le(izbox, field):
    assert_query_equals(Filesystem.find(izbox, field <= "X"), "id=le%3AX")


def test_querying_gt(izbox, field):
    assert_query_equals(Filesystem.find(izbox, field > "X"), "id=gt%3AX")


def test_querying_lt(izbox, field):
    assert_query_equals(Filesystem.find(izbox, field < "X"), "id=lt%3AX")


def _get_expectation_with_range(field_name, operator_name, iterable):
    return field_name + "=" + operator_name + "%3A%28" + "%2C".join(str(item) for item in iterable) + "%29"


def test_querying_between(izbox, field):
    id_range = (1, 3)
    expected = _get_expectation_with_range("id", "between", id_range)
    assert_query_equals(
        Filesystem.find(izbox, field.__between__(id_range)), expected)
    assert_query_equals(
        Filesystem.find(izbox, field.between(id_range)), expected)


def test_querying_like(izbox, field):
    field = izbox.objects.filesystems.fields.name
    assert_query_equals(
        Filesystem.find(izbox, field.like("abc")), "name=like%3Aabc")


def test_querying_in(izbox, field):
    id_range = (1, 3)
    expected = _get_expectation_with_range("id", "in", id_range)
    assert_query_equals(Filesystem.find(izbox, field.in_(id_range)), expected)


def test_querying_not_in(izbox, field):
    id_range = (1, 3)
    expected = _get_expectation_with_range("id", "notin", id_range)
    assert_query_equals(
        Filesystem.find(izbox, field.not_in(id_range)), expected)


def test_sorting(izbox, field):
    assert_query_equals(
        Filesystem.find(izbox).sort(-Filesystem.fields.quota), "sort=-quota_in_bytes")
    assert_query_equals(
        Filesystem.find(izbox).sort(+Filesystem.fields.quota), "sort=quota_in_bytes")
    assert_query_equals(
        Filesystem.find(izbox).sort(Filesystem.fields.quota), "sort=quota_in_bytes")


def test_sorting_multiple(izbox, field):
    assert_query_equals(
        Filesystem.find(izbox).sort(-Filesystem.fields.quota, +Filesystem.fields.id), "sort=-quota_in_bytes%2Cid")


def test_only_fields(izbox, field):
    # NOTE: uses api name!
    assert_query_equals(
        Filesystem.find(izbox).only_fields(["quota"]), "fields=id%2Cquota_in_bytes")


def test_pagination(izbox, field):
    assert_query_equals(
        Filesystem.find(izbox).page(5).page_size(100), None)  # pages are only added at query


def assert_query_equals(q, expected):
    if expected is not None:
        expected = "?{0}".format(expected)
    else:
        expected = ""
    assert q.query == ('/api/rest/filesystems' + expected)


def test_negative_item_position(izbox, field):
    with pytest.raises(NotImplementedError):
        izbox.events.find()[-3]


def test_paged_query_traversal(izbox):
    """
    Makes sure that traversing a paged query only returns the requested page
    """
    page_size = 10
    result = izbox.components.find().page(5).page_size(page_size)
    assert len(result) == page_size
