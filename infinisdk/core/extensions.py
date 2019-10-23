# !
# Infinidat Ltd.  -  Proprietary and Confidential Material
# Copyright (C) 2015, Infinidat Ltd. - All Rights Reserved
# NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
# All information contained herein is protected by trade secret or copyright law.
# The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
# and may be protected by U.S. and Foreign Patents, or patents in progress.
# Redistribution and use in source or binary forms, with or without modification,
# are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
# !
import functools

from sentinels import NOTHING

active = []


def _extend_method(objtype, name, wrap):
    def decorator(func):
        method_name = name
        if method_name is None:
            method_name = func.__name__

        extension = Method(objtype, method_name, func, wrap)
        extension.activate()
        func.__extension_deactivate__ = extension.deactivate
        return func
    return decorator


def add_method(objtype, name=None):
    return _extend_method(objtype, name, False)


def wrap_method(objtype, name=None):
    return _extend_method(objtype, name, True)


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


class Attachment:

    def __init__(self, objtype, name, func, wrap=False):
        super(Attachment, self).__init__()
        assert isinstance(objtype, type)
        if wrap and not hasattr(objtype, name):
            raise RuntimeError(
                'You asked to wrap {1!r} in {0.__name__}, but it doesn\'t have such a method'.format(objtype, name))
        self._objtype = objtype
        self._name = name
        self._func = func
        self._active = False
        self._wrap = wrap
        self._original = None

    def activate(self):
        assert self not in active
        if self._wrap:
            self._original = getattr(self._objtype, self._name)
        setattr(self._objtype, self._name, self)
        self._active = True
        active.append(self)

    def deactivate(self):
        if not self._active:
            return
        assert self._objtype.__dict__[self._name] is self
        if self._wrap:
            setattr(self._objtype, self._name, self._original)
        else:
            delattr(self._objtype, self._name)
            assert self._name not in self._objtype.__dict__
        self._active = False
        active.remove(self)

    def __repr__(self):
        return "<{}:{}>".format(self._objtype.__name__, self._name)


class Method(Attachment):

    def __get__(self, obj, objclass):
        kwargs = {}
        if self._wrap:
            assert self._original
            kwargs['_wrapped'] = self._original

        # pylint: disable=attribute-defined-outside-init
        method = _BoundMethod(self._func, obj, **kwargs)
        method.__name__ = self._name
        method.__self__ = method.im_self = obj
        method.im_class = objclass
        method.im_func = self._func
        return method


class _BoundMethod(functools.partial):  # pylint: disable=inherit-non-class

    @property
    def __doc__(self):
        return self.func.__doc__

    def __repr__(self):
        # pylint: disable=missing-format-attribute
        return '<Bound method {0.im_class.__name__}.{0.__name__} of {0.args[0]!r}>'.format(self)



_PROPERTY_CACHE = "__property_cache__"

class Property(Attachment):

    def __get__(self, obj, objclass):
        caching = obj.__dict__.setdefault(_PROPERTY_CACHE, {})
        cached = caching.get(self, NOTHING)
        if cached is NOTHING:
            cached = self._func(obj)
            caching[self] = cached
        return cached
