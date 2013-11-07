import time
import itertools

from ..._compat import iteritems


class SpecialValue(object):
    pass

OMIT = SpecialValue()

class Autogenerate(SpecialValue):

    _ORDINALS = {}

    def __init__(self, template):
        super(Autogenerate, self).__init__()
        self.template = template

    def generate(self):
        counter = self._ORDINALS.get(self.template, None)
        if counter is None:
            counter = self._ORDINALS[self.template] = itertools.count(1)
        return self.template.format(time=time.time(), ordinal=next(counter))


def translate_special_values(d):
    for key, value in list(iteritems(d)):
        if isinstance(value, dict):
            translate_special_values(value)
        elif isinstance(value, SpecialValue):
            if value is OMIT:
                d.pop(key)
            elif isinstance(value, Autogenerate):
                d[key] = value.generate()
            else:
                raise NotImplementedError() # pragma: no cover
    return d
