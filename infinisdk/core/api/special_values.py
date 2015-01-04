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
import itertools
import flux
from uuid import uuid1

from api_object_schema.special_value import SpecialValue

from ..._compat import iteritems


OMIT = SpecialValue()

class Autogenerate(SpecialValue):
    """
    Designates a value that should be autogenerated upon request. The argument to the constructor is a
    template string. When formatted, these fields can be used:

    - ordinal: the number of times this template has been used already in this session
    - time: the current time, as a floating point number
    - timestamp: an integral value designating the current time (milliseconds)
    - uuid: a unique identifier generated from uuid1
    """

    _ORDINALS = {}

    def __init__(self, template):
        super(Autogenerate, self).__init__()
        self.template = template

    def generate(self):
        counter = self._ORDINALS.get(self.template, None)
        if counter is None:
            counter = self._ORDINALS[self.template] = itertools.count(1)
        current_time = flux.current_timeline.time()
        return self.template.format(time=current_time, timestamp=int(current_time * 1000), ordinal=next(counter), uuid=_LAZY_UUID_FACTORY)

class RawValue(SpecialValue):
    def __init__(self, value):
        super(RawValue, self).__init__()
        self._value = value
    def generate(self):
        return self._value
    def __str__(self):
        return "<RawValue {}>".format(self._value)

class _LazyUUIDFactory(object):
    def __str__(self):
        return str(uuid1()).lower().replace("-", "")

_LAZY_UUID_FACTORY = _LazyUUIDFactory()

def translate_special_values_dict(data_dict):
    for key, value in list(iteritems(data_dict)):
        if value is OMIT:
            data_dict.pop(key)
        else:
            data_dict[key] = translate_special_values(value)
    return data_dict

def translate_special_values(data):
    if isinstance(data, dict):
        return translate_special_values_dict(data)
    elif isinstance(data, SpecialValue):
        if isinstance(data, Autogenerate):
            return data.generate()
        raise NotImplementedError() # pragma: no cover
    return data
