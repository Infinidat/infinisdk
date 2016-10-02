import operator
import pytest

from infinisdk.core.exceptions import ObjectNotFound, TooManyObjectsFound
from ..conftest import create_volume

# pylint: disable=redefined-outer-name


def test_querying_length(infinibox):
    Volume = infinibox.volumes.object_type
    assert len(Volume.find(infinibox)) == 0
    create_volume(infinibox, name="vol1")
    assert len(Volume.find(infinibox)) == 1


def test_get_too_many_items(infinibox):
    for i in range(2):
        create_volume(infinibox, name="vol{0}".format(i))
    with pytest.raises(TooManyObjectsFound):
        infinibox.objects.volumes.get()


def test_get_not_found(infinibox):
    with pytest.raises(ObjectNotFound):
        infinibox.objects.volumes.get(name="nonexisting")
    assert infinibox.objects.volumes.safe_get(name="nonexisting") is None


def test_choose_not_found(infinibox):
    with pytest.raises(ObjectNotFound):
        infinibox.objects.volumes.choose(name="nonexisting")
    assert infinibox.objects.volumes.safe_choose(name="nonexisting") is None


@pytest.fixture
def field(infinibox):
    return infinibox.objects.volumes.fields.id


def test_querying_equal(infinibox, field):
    for query in [
            infinibox.volumes.find(id=2),
            infinibox.volumes.find(field == 2),  # pylint: disable=no-member
    ]:
        assert_query_equals(query, "id=eq%3A2")


def test_unknown_fields(infinibox):
    assert_query_equals(infinibox.volumes.find(unknown_field=2),
                        "unknown_field=eq%3A2")


@pytest.mark.parametrize('operator', [operator.ne, operator.ge, operator.le, operator.gt, operator.lt])
def test_querying_operation(infinibox, field, operator):
    operand = 123
    assert_query_equals(infinibox.volumes.find(operator(field, operand)),
                        "id={0}%3A{1}".format(operator.__name__, operand))


def _get_expectation_with_range(field_name, operator_name, iterable):
    return field_name + "=" + operator_name + "%3A%28" + "%2C".join(str(item) for item in iterable) + "%29"


def test_querying_between(infinibox, field):
    id_range = (1, 3)
    expected = _get_expectation_with_range("id", "between", id_range)
    assert_query_equals(
        infinibox.volumes.find(field.__between__(id_range)), expected)
    assert_query_equals(
        infinibox.volumes.find(field.between(id_range)), expected)


def test_querying_like(infinibox, field):
    field = infinibox.objects.volumes.fields.name
    assert_query_equals(
        infinibox.volumes.find(field.like("abc")), "name=like%3Aabc")


def test_querying_in(infinibox, field):
    id_range = (1, 3)
    expected = _get_expectation_with_range("id", "in", id_range)
    assert_query_equals(infinibox.volumes.find(field.in_(id_range)), expected)


def test_querying_not_in(infinibox, field):
    id_range = (1, 3)
    expected = _get_expectation_with_range("id", "notin", id_range)
    assert_query_equals(
        infinibox.volumes.find(field.not_in(id_range)), expected)


def test_sorting(infinibox):
    # pylint: disable=no-member
    Volume = infinibox.volumes.object_type
    assert_query_equals(
        Volume.find(infinibox).sort(-Volume.fields.used_size), "sort=-used")
    assert_query_equals(
        Volume.find(infinibox).sort(+Volume.fields.used_size), "sort=used")
    assert_query_equals(
        Volume.find(infinibox).sort(Volume.fields.used_size), "sort=used")


def test_sorting_multiple(infinibox):
    # pylint: disable=no-member
    Volume = infinibox.volumes.object_type
    assert_query_equals(
        Volume.find(infinibox).sort(-Volume.fields.used_size, +Volume.fields.id), "sort=-used%2Cid")


def test_only_fields(infinibox):
    Volume = infinibox.volumes.object_type
    lazy_query = Volume.find(infinibox).only_fields(["used_size"])  # NOTE: uses api name!
    assert str(lazy_query.query.path) == '/api/rest/volumes'
    assert list(lazy_query.query.query_dict) == ['fields']
    assert set(['id', 'used']) == set(lazy_query.query.query_dict['fields'].split(','))


def test_pagination(infinibox):
    assert_query_equals(infinibox.volumes.find().page(5).page_size(100), None)  # pages are only added at query


def assert_query_equals(q, expected):
    if expected is not None:
        expected = "?{0}".format(expected)
    else:
        expected = ""
    assert q.query == ('/api/rest/volumes' + expected)


def test_negative_item_position(infinibox):
    with pytest.raises(NotImplementedError):
        infinibox.events.find()[-3]  # pylint: disable=expression-not-assigned


def test_paged_query_traversal(infinibox):
    """
    Makes sure that traversing a paged query only returns the requested page
    """
    page_size = 1
    result = infinibox.users.find().page(3).page_size(page_size)
    assert len(result) == page_size
