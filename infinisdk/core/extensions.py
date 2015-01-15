# !
# Infinidat Ltd.  -  Proprietary and Confidential Material
###
# Copyright (C) 2015, Infinidat Ltd. - All Rights Reserved
###
# NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
# All information contained herein is protected by trade secret or copyright law.
# The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
# and may be protected by U.S. and Foreign Patents, or patents in progress.
###
# Redistribution and use in source or binary forms, with or without modification,
# are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
# !
import functools

from sentinels import NOTHING

active = []


def add_method(objtype, name=None):
    def decorator(func):
        method_name = name
        if method_name is None:
            method_name = func.__name__

        extension = Method(objtype, method_name, func)
        extension.activate()
        func.__extension_deactivate__ = extension.deactivate
        return func
    return decorator


def add_attribute(objtype, name=None):
    def decorator(property_func):
        property_name = name
        if property_name is None:
            property_name = property_func.__name__

        extension = Property(objtype, property_name, property_func)
        extension.activate()
        property_func.__extension_deactivate__ = extension.deactivate
        return property_func
    return decorator


def clear_all():
    for x in list(active):
        x.deactivate()
    assert not active


class Attachment(object):

    def __init__(self, objtype, name, func):
        super(Attachment, self).__init__()
        assert isinstance(objtype, type)
        if name in objtype.__dict__:
            raise RuntimeError(
                '{0.__name__} already has a method named {1!r}. Cannot attach as extension.'.format(objtype, name))
        assert name not in objtype.__dict__
        self._objtype = objtype
        self._name = name
        self._func = func
        self._active = False

    def activate(self):
        assert self not in active
        setattr(self._objtype, self._name, self)
        self._active = True
        active.append(self)

    def deactivate(self):
        if not self._active:
            return
        assert self._objtype.__dict__[self._name] is self
        delattr(self._objtype, self._name)
        self._active = False
        active.remove(self)
        assert self._name not in self._objtype.__dict__

    def __repr__(self):
        return "<{0}:{1}>".format(self._objtype.__name__, self._name)


class Method(Attachment):

    def __get__(self, obj, objclass):
        method = functools.partial(self._func, obj)
        method.__self__ = method.im_self = obj
        method.im_class = objclass
        method.im_func = self._func
        return method


class Property(Attachment):

    def __init__(self, *args, **kwargs):
        super(Property, self).__init__(*args, **kwargs)
        self._cache = {}

    def __get__(self, obj, objclass):
        cached = self._cache.get(obj, NOTHING)
        if cached is NOTHING:
            cached = self._func(obj)
            self._cache[obj] = cached
        return cached
