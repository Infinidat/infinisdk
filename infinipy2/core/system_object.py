from .._compat import with_metaclass
from .fields import FieldsMeta

class SystemObject(with_metaclass(FieldsMeta)):
    FIELDS = []
