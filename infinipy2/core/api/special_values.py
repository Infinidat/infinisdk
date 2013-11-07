from ..._compat import iteritems

class SpecialValue(object):
    pass

OMIT = SpecialValue()

def translate_special_values(d):
    for key, value in list(iteritems(d)):
        if isinstance(value, dict):
            translate_special_values(value)
        elif value is OMIT:
            d.pop(key)
    return d
