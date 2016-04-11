import pytest
import logbook

# pylint: disable=redefined-outer-name

@pytest.mark.parametrize('operation', [
    lambda infinibox: list(infinibox.volumes.find(name='nonexistent')),
    lambda infinibox: infinibox.volumes.safe_get(name='nonexistent'),
])
def test_len_caching_on_empty_lists(infinibox, operation):
    with logbook.TestHandler() as handler:
        result = operation(infinibox)
        assert not result

    [r] = [record for record in handler.records if '<-- GET http://' in record.message] # pylint: disable=unused-variable


def test_lazy_query_out_of_bounds_with_first_checking_length(result, page_size):
    assert len(result) > page_size
    with pytest.raises(IndexError):
        result[len(result) + 1]  # pylint: disable=expression-not-assigned


def test_lazy_query_out_of_bounds_without_first_checking_length(result):
    with pytest.raises(IndexError):
        result[len(result) + 1]  # pylint: disable=expression-not-assigned


def test_lazy_query(result, page_size):
    pages_total = (len(result) // page_size)  # pylint: disable=unused-variable
    if float(len(result)) / page_size != 0:
        pages_total += 1

    assert len(result) > page_size

    assert_fetched(result, [0], page_size)

    assert result[(page_size + 1)] is not None

    assert_fetched(result, [0, 1], page_size)


def assert_fetched(result, pages, page_size):
    # pylint: disable=protected-access
    for i in range(0, len(result), page_size):
        if i // page_size in pages:
            assert result._fetched[
                i] is not None, 'Object {0} not fetched as expected'.format(i)
        else:
            assert result._fetched.get(
                i) is None, "Object {0} unexpectedly fetched".format(i)


@pytest.fixture
def page_size():
    return 2


@pytest.fixture
def result(infinibox, page_size):
    infinibox.users.create()
    return infinibox.users.find().page_size(page_size)
