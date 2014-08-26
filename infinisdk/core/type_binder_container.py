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
from .._compat import string_types, itervalues


class TypeBinderContainer(object):
    """
    Contains several type binders with a common characteristic. Used to implement system.objects and similar facilities
    """

    def __init__(self, system):
        super(TypeBinderContainer, self).__init__()
        self.system = system
        self._binders_by_class = {}
        self._binders_by_name = {}

    def install(self, object_type):
        binder = object_type.bind(self.system)
        self._binders_by_class[object_type] = binder
        self._binders_by_name[object_type.get_plural_name()] = binder
        assert not hasattr(self.system, object_type.get_plural_name())
        setattr(self.system, object_type.get_plural_name(), binder)

    def __getattr__(self, attr):
        """
        Gets a type binder given its name
        """
        try:
            return self._binders_by_name[attr]
        except LookupError:
            raise AttributeError(attr)

    def __getitem__(self, name):
        """
        Gets a type binder given its name
        """
        if isinstance(name, string_types):
            return self._binders_by_name[name]
        return self._binders_by_class[name]

    def __iter__(self):
        return itervalues(self._binders_by_name)

    def __len__(self):
        return len(self._binders_by_name)

    def get_types(self):
        return list(self._binders_by_class)
