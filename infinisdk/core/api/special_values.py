import itertools
import flux
from uuid import uuid4

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
    - uuid: a unique identifier generated from uuid4
    - short_uuid: a short (hopefully) unique identifier
    - prefix: a prefix added to all generated values, will be added to template unless defined in the given template
    """

    _prefix = ''
    _ORDINALS = {}

    def __init__(self, template):
        super(Autogenerate, self).__init__()
        if '{prefix}' not in template:
            template = '{prefix}' + template
        self.template = template

    def generate(self):
        counter = self._ORDINALS.get(self.template, None)
        if counter is None:
            counter = self._ORDINALS[self.template] = itertools.count(1)
        current_time = flux.current_timeline.time()
        return self.template.format(time=current_time, timestamp=int(current_time * 1000), ordinal=next(counter), uuid=_LAZY_UUID_FACTORY, short_uuid=_LAZY_SHORT_UUID_FACTORY, prefix=self._prefix)

    @classmethod
    def set_prefix(cls, prefix):
        if prefix:
            cls._prefix = prefix
        else:
            prefix = ''

    @classmethod
    def get_prefix(cls):
        return cls._prefix


class RawValue(SpecialValue):
    def __init__(self, value):
        super(RawValue, self).__init__()
        self._value = value

    def generate(self):
        return self._value

    def __repr__(self):
        return "<RawValue {}>".format(self._value)


class _LazyUUIDFactory(object):

    def __init__(self, short=False):
        super(_LazyUUIDFactory, self).__init__()
        self._short = short

    def __str__(self):
        returned = str(uuid4()).lower().replace("-", "")
        if self._short:
            returned = returned[:4]
        return returned


_LAZY_UUID_FACTORY = _LazyUUIDFactory()
_LAZY_SHORT_UUID_FACTORY = _LazyUUIDFactory(short=True)



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
        if isinstance(data, Autogenerate) or isinstance(data, RawValue):
            return data.generate()
        raise NotImplementedError() # pragma: no cover
    return data
