import pytest
import sys
from infinisdk.core.api.special_values import OMIT, Autogenerate, RawValue
from infinisdk.core.utils import add_comma_separated_query_param, add_normalized_query_params
from infinisdk.core.utils.environment import get_logged_in_username


def test_add_comma_separated_query_param():
    assert add_comma_separated_query_param(
        "http://a.com/a/b/c", "sort", "a") == 'http://a.com/a/b/c?sort=a'
    assert add_comma_separated_query_param(
        "http://a.com/a/b/c?sort=a", "sort", "b") == 'http://a.com/a/b/c?sort=a%2Cb'


def test_get_logged_in_username():
    assert isinstance(get_logged_in_username(), str)


def test_add_normalized_query_params():
    if sys.version_info[:2] < (3, 6):
        pytest.skip("Dictionaries are not ordered")
    assert add_normalized_query_params(
        "http://a.com", some_key=True, other_key=False) == "http://a.com?some_key=true&other_key=false"
    assert add_normalized_query_params(
        "http://a.com", some_key=OMIT, other_key=RawValue(True)) == "http://a.com?other_key=True"
    auto_gen = Autogenerate("a_{ordinal}")
    assert add_normalized_query_params(
        "http://a.com?pre=3", some_key=5, other_key=auto_gen) == "http://a.com?pre=3&some_key=5&other_key=a_1"
