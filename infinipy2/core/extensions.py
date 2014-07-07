import functools

active = []

def add_method(objtype, name=None):
    def decorator(func):
        method_name = name
        if method_name is None:
            method_name = func.__name__

        extension = Method(objtype, method_name, func)
        extension.activate()
        if not hasattr(func, 'remove'):
            func.deactivate = extension.deactivate
        return func
    return decorator

def clear_all():
    for x in list(active):
        x.deactivate()
    assert not active

class Method(object):

    def __init__(self, objtype, name, func):
        super(Method, self).__init__()
        assert isinstance(objtype, type)
        assert name not in objtype.__dict__
        self._objtype = objtype
        self._name = name
        self._func = func
        self._active = False

    def __get__(self, obj, objclass):
        return functools.partial(self._func, obj)

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
