import itertools

from sentinels import NOTHING

from .._compat import with_metaclass, iteritems, itervalues
from .fields import FieldsMeta
from .object_query import ObjectQuery
from .type_binder import TypeBinder
from urlobject import URLObject as URL

class SystemObject(with_metaclass(FieldsMeta)):
    FIELDS = []
    URL_PATH = None
    #: specifies which :class:`.TypeBinder` subclass is to be used for this type
    BINDER_CLASS = TypeBinder

    def __init__(self, system, initial_data):
        super(SystemObject, self).__init__()
        #: the system to which this object belongs
        self.system = system
        self._cache = initial_data
        self.id = self._cache[self.fields.id.api_name]

    @classmethod
    def create(cls, system, **fields):
        return cls(system, system.api.post(cls.get_url_path(system), data=cls._get_data_for_post(fields)).get_result())

    @classmethod
    def _get_data_for_post(cls, fields):
        returned = {}
        for field in cls.fields:
            if not field.mandatory and field.name not in fields:
                continue
            field_value = fields.get(field.name, NOTHING)
            if field_value is NOTHING:
                field_value = field.get_default(system)
            returned[field.api_name] = field.translator.to_api(field_value)
        return returned

    @classmethod
    def bind(cls, system):
        return cls.BINDER_CLASS(cls, system)

    @classmethod
    def get_plural_name(cls):
        return cls.__name__.lower() + "s"

    @classmethod
    def get_url_path(cls, system):
        url_path = cls.URL_PATH
        if url_path is None:
            url_path = "/api/rest/{}".format(cls.get_plural_name())
        return url_path

    @classmethod
    def find(cls, system, *predicates, **kw):
        url = URL(cls.get_url_path(system))
        if kw:
            predicates = itertools.chain(
                predicates,
                (getattr(cls.fields, key) == value for key, value in iteritems(kw)))
        for pred in predicates:
            url = pred.add_to_url(url)

        return ObjectQuery(system, url, cls)

    def get_field(self, field_name, from_cache=False):
        """
        Gets the value of a single field from the system

        :param cache: Attempt to use the last cached version of the field value
        """
        return self.get_fields([field_name], from_cache=from_cache)[field_name]

    def get_fields(self, field_names, from_cache=False):
        """
        Gets a set of fields from the system

        :param from_cache: Attempt to fetch the fields from the cache
        :rtype: a dictionary of field names to their values
        """
        if from_cache:
            returned = {field_name: self._cache.get(self.fields[field_name].api_name, NOTHING) for field_name in field_names}
            if not any(x is NOTHING for x in itervalues(returned)):
                return returned

        # TODO: remove unnecessary construction
        [result] = self.find(self.system, id=self.id).only_fields(field_names)

        self._cache.update(result._cache)

        returned = {}
        for field_name in field_names:
            field = self.fields[field_name]
            returned[field_name] = field.translator.from_api(self._cache[field.api_name])

        return returned

    def __repr__(self):
        return "<{} id={}>".format(type(self).__name__, self.id)
