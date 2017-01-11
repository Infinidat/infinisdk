from urlobject import URLObject as URL
from collections import Iterable
from ..._compat import string_types


def add_comma_separated_query_param(url, param_name, value):
    """
    >>> str(add_comma_separated_query_param("http://a.com/a/b/c", "sort", "a"))
    'http://a.com/a/b/c?sort=a'
    >>> str(add_comma_separated_query_param("http://a.com/a/b/c?sort=a", "sort", "b"))
    'http://a.com/a/b/c?sort=a%2Cb'
    >>> str(add_comma_separated_query_param("http://a.com/a/b/c", "sort", ("a", "b")))
    'http://a.com/a/b/c?sort=a%2Cb'
    """
    if not isinstance(url, URL):
        url = URL(url)
    if isinstance(value, Iterable) and not isinstance(value, string_types):
        value = ",".join(value)
    existing_sort = url.query_dict.get(param_name, "")
    if existing_sort:
        existing_sort = "{0},".format(existing_sort)

    return url.set_query_param(param_name, "{0}{1}".format(existing_sort, value))
