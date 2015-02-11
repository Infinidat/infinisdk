import pytest

from infinisdk.core.utils import add_comma_separated_query_param


def test_add_comma_separated_query_param():
    assert add_comma_separated_query_param(
        "http://a.com/a/b/c", "sort", "a") == 'http://a.com/a/b/c?sort=a'
    assert add_comma_separated_query_param(
        "http://a.com/a/b/c?sort=a", "sort", "b") == 'http://a.com/a/b/c?sort=a%2Cb'


