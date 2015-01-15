###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from urlobject import URLObject as URL


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
    if isinstance(value, (list, tuple)):
        value = ",".join(value)
    existing_sort = url.query_dict.get(param_name, "")
    if existing_sort:
        existing_sort = "{0},".format(existing_sort)

    return url.set_query_param(param_name, "{0}{1}".format(existing_sort, value))
