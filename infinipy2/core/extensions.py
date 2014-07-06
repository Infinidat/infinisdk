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
        assert not hasattr(objtype, name)
        self._objtype = objtype
        self._name = name
        self._func = func

    def __get__(self, obj, objclass):
        return functools.partial(self._func, obj)

    def activate(self):
        assert self not in active
        setattr(self._objtype, self._name, self)
        active.append(self)

    def deactivate(self):
        delattr(self._objtype, self._name)
        active.remove(self)
