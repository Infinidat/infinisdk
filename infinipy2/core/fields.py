from .._compat import itervalues, iterkeys

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
        self._fields_by_api_name = {}
        self._identity_fields = []

    def update(self, other_fields):
        for field in other_fields:
            self.add_field(field)

    def add_field(self, field):
        self._fields[field.name] = field
        self._fields_by_api_name[field.api_name] = field
        if field.is_identity:
            self._identity_fields.append(field)

    def get_identity_fields(self):
        return self._identity_fields

    def get_all_field_names(self, api_object_json):
        """
        Given an example of an object from the system's API, returns the formal set of field names supported
        by this object type (after transformation to logical names)
        """
        returned = set()
        for field_name in api_object_json:
            logical_field = self._fields_by_api_name.get(field_name)
            if logical_field is not None:
                field_name = logical_field.name
            returned.add(field_name)
        return returned

    def get(self, field_name, default=None):
        return self._fields.get(field_name, default)

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
