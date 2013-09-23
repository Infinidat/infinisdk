import itertools
from .._compat import with_metaclass, iteritems
from .fields import FieldsMeta
from .object_query import ObjectQuery
from urlobject import URLObject as URL

class SystemObject(with_metaclass(FieldsMeta)):
    FIELDS = []
    URL_PATH = None

    def __init__(self, system, initial_data):
        super(SystemObject, self).__init__()
        #: the system to which this object belongs
        self.system = system
        self._cache = initial_data
        self.id = self._get_id_from_cache()

    def _get_id_from_cache(self):
        return self._cache["id"] # TODO: this needs to rely on FIELDS

    @classmethod
    def get_url_path(cls, system):
        url_path = cls.URL_PATH
        if url_path is None:
            url_path = "/api/rest/{}s".format(cls.__name__.lower())
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
