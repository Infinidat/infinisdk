from . import field


class _Q:

    def __getattribute__(self, name):
        if name.startswith("_"):
            return super(_Q, self).__getattribute__(name)
        return QField(name)

Q = _Q()

class QField(field.Field):
    pass
