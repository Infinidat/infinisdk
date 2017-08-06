from infinisdk.core.utils import add_comma_separated_query_param
from infinisdk.core.utils.environment import get_logged_in_username


def test_add_comma_separated_query_param():
    assert add_comma_separated_query_param(
        "http://a.com/a/b/c", "sort", "a") == 'http://a.com/a/b/c?sort=a'
    assert add_comma_separated_query_param(
        "http://a.com/a/b/c?sort=a", "sort", "b") == 'http://a.com/a/b/c?sort=a%2Cb'


def test_get_logged_in_username():
    assert isinstance(get_logged_in_username(), str)
