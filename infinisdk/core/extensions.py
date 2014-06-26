###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
import functools

active = []

def add_method(objtype, name=None):
    def decorator(func):
        method_name = name
        if method_name is None:
            method_name = func.__name__

        extension = Method(objtype, method_name, func)
        extension.activate()
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
