import pytest


def test_lazy_query_out_of_bounds_with_first_checking_length(result, page_size):
    assert len(result) > page_size
    with pytest.raises(IndexError):
        result[len(result) + 1]


def test_lazy_query_out_of_bounds_without_first_checking_length(result, page_size):
    with pytest.raises(IndexError):
        result[len(result) + 1]


def test_lazy_query(result, page_size):
    page_size = 10
    pages_total = (len(result) // page_size)
    if float(len(result)) / page_size != 0:
        pages_total += 1

    assert len(result) > page_size

    assert_fetched(result, [0], page_size)

    assert result[(page_size + 1)] is not None

    assert_fetched(result, [0, 1], page_size)


def assert_fetched(result, pages, page_size):
    for i in range(0, len(result), page_size):
        if i // page_size in pages:
            assert result._fetched[
                i] is not None, 'Object {0} not fetched as expected'.format(i)
        else:
            assert result._fetched.get(
                i) is None, "Object {0} unexpectedly fetched".format(i)


@pytest.fixture
def page_size():
    return 10


@pytest.fixture
def result(izbox, page_size):
    return izbox.components.find().page_size(page_size)
