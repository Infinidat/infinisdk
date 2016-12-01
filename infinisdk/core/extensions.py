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
        method = _BoundMethod(self._func, obj)
        method.__name__ = self._name
        method.__self__ = method.im_self = obj
        method.im_class = objclass
        method.im_func = self._func
        return method


class _BoundMethod(functools.partial):

    @property
    def __doc__(self):
        return self.func.__doc__

    def __repr__(self):
        return '<Bound method {0.im_class.__name__}.{0.__name__} of {0.args[0]!r}>'.format(self)



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
