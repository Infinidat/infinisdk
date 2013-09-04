from .._compat import itervalues

class FieldsMeta(type):

    def __new__(cls, classname, bases, classdict):
        returned = type.__new__(cls, classname, bases, classdict)
        returned.fields = fields = Fields()
        for base in bases:
            if not isinstance(base, FieldsMeta):
                continue
            fields.update(base.fields)

        for field in classdict.get("FIELDS", []):
            fields.add_field(field)

        return returned

class Fields(object):

    def __init__(self):
        super(Fields, self).__init__()
        self._fields = {}

    def update(self, other_fields):
        for field in other_fields:
            self._fields[field.name] = field

    def add_field(self, field):
        self._fields[field.name] = field

    def __getattr__(self, attr):
        try:
            return self[attr]
        except LookupError:
            raise AttributeError(attr)

    def __getitem__(self, item):
        return self._fields[item]

    def __iter__(self):
        return itervalues(self._fields)

    def __len__(self):
        return len(self._fields)
