from urlobject import URLObject as URL
from ..._compat import string_types, abc_module


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
    if isinstance(value, abc_module.Iterable) and not isinstance(value, string_types):
        value = ",".join(value)
    existing_sort = url.query_dict.get(param_name, "")
    if existing_sort:
        existing_sort = "{},".format(existing_sort)

    return url.set_query_param(param_name, "{}{}".format(existing_sort, value))
