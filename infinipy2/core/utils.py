import functools
import itertools
import time

from urlobject import URLObject as URL


def add_comma_separated_query_param(url, param_name, value):
    """
    >>> str(add_comma_separated_query_param("http://a.com/a/b/c", "sort", "a"))
    'http://a.com/a/b/c?sort=a'
    >>> str(add_comma_separated_query_param("http://a.com/a/b/c?sort=a", "sort", "b"))
    'http://a.com/a/b/c?sort=a%2Cb'
    """
    if not isinstance(url, URL):
        url = URL(url)
    if isinstance(value, (list, tuple)):
        value = ",".join(value)
    existing_sort = url.query_dict.get(param_name, "")
    if existing_sort:
        existing_sort = "{0},".format(existing_sort)

    return url.set_query_param(param_name, "{0}{1}".format(existing_sort, value))

def get_name_generator(template="obj-{ordinal}-{time}"):
    return functools.partial(generate_name, template)

def generate_name(template):
    return template.format(time=time.time(), ordinal=_OrdinalGetter(template))

class _OrdinalGetter(object):

    _ORDINALS = {}

    def __init__(self, key):
        self.key = key

    def __str__(self):
        counter = self._ORDINALS.get(self.key, None)
        if counter is None:
            counter = self._ORDINALS[self.key] = itertools.count(1)
        return str(next(counter))
