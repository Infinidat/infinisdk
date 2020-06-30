import collections
from urlobject import URLObject as URL
from ..api.special_values import OMIT, Autogenerate, RawValue


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
    if isinstance(value, collections.abc.Iterable) and not isinstance(value, (str, bytes)):
        value = ",".join(value)
    existing_sort = url.query_dict.get(param_name, "")
    if existing_sort:
        existing_sort = "{},".format(existing_sort)

    return url.set_query_param(param_name, "{}{}".format(existing_sort, value))


def normalized_query_value(value):
    norm_value = value
    if isinstance(norm_value, (RawValue, Autogenerate)):
        norm_value = norm_value.generate()
    elif isinstance(norm_value, bool):
        norm_value = str(norm_value).lower()
    return norm_value


def add_normalized_query_params(url, **kwargs):
    url = URL(url)
    for key, value in kwargs.items():
        if value is OMIT:
            continue
        norm_value = normalized_query_value(value)
        url = url.add_query_param(key, norm_value)
    return url
