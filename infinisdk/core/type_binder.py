import random
from contextlib import contextmanager
from sentinels import NOTHING
from urlobject import URLObject

from .object_query import PolymorphicQuery, ObjectQuery
from .exceptions import ObjectNotFound, TooManyObjectsFound


class BaseBinder:
    """
    Binds a specific type to a system.
    """

    def __init__(self, system):
        super(BaseBinder, self).__init__()
        self.system = system

    def is_caching_enabled(self):
        return False

    def get_url_path(self):
        raise NotImplementedError()

    def is_supported(self):
        raise NotImplementedError()

    def find(self, *predicates, **kw):
        raise NotImplementedError()

    def get_all(self):
        return self.find()

    def get_by_id(self, id):  # pylint: disable=redefined-builtin
        """
        Obtains an object with a specific id
        """
        return self.get(id=id)

    def safe_get_by_id(self, id):  # pylint: disable=redefined-builtin
        """
        Like get_by_id, only returning None if the object could not be found
        """
        return self.safe_get(id=id)

    def get(self, *predicates, **kw):
        """
        Finds exactly one object matching criteria. Raises :class:`.ObjectNotFound` if not found,
        :class:`.TooManyObjectsFound` if more than one is found
        """
        returned = self.find(*predicates, **kw)
        if not returned:
            raise ObjectNotFound(str(returned))
        if len(returned) > 1:
            raise TooManyObjectsFound(str(returned))
        [obj] = returned
        return obj

    def safe_get(self, *predicates, **kw):
        """
        Like :meth:`.get`, only returns ``None`` if no objects were found
        """
        try:
            return self.get(*predicates, **kw)
        except ObjectNotFound:
            return None

    def sample(self, *predicates, **kw):
        """
        Chooses a random sample out of those returned. Raises ValueError if there are not enough items
        """
        sample_count = kw.pop('sample_count', 1)
        return self.find(*predicates, **kw).sample(sample_count)

    def choose(self, *predicates, **kw):
        """
        Chooses a random element out of those returned. Raises ObjectNotFound if none were returned
        """
        returned = self.find(*predicates, **kw)
        if not returned:
            raise ObjectNotFound(str(returned))

        return returned[random.randrange(len(returned))]

    def safe_choose(self, *predicates, **kw):
        """
        Like choose, but returns None when not found
        """
        try:
            return self.choose(*predicates, **kw)
        except ObjectNotFound:
            return None

    def count(self, *predicates, **kw):
        return self.find(*predicates, **kw).count()

    def __iter__(self):
        return iter(self.find())

    def to_list(self):
        """Returns the entire set of objects as a Python list

        .. caution:: Queries are lazy by default to avoid heavy API calls and repetitive page
          requests. Using ``to_list`` will forcibly iterate and fetch all objects, which might
          be a very big collection. This can cause issues like slowness and memory exhaustion
        """
        return self.get_all().to_list()


class PolymorphicBinder(BaseBinder):

    def __init__(self, url, object_types, factory, system, feature_name=NOTHING):
        super(PolymorphicBinder, self).__init__(system)
        self._object_types = object_types
        self._url = URLObject(url)
        self._query_factory = factory
        self._feature_name = feature_name

    def __repr__(self):
        return "<{}.{} ({})>".format(self.system, self.__class__.__name__,
                                     " & ".join(type_.get_plural_name() for type_ in self._object_types))

    def get_url_path(self):
        return self._url

    def is_supported(self):
        return True

    def find(self, *predicates, **kw):
        query = PolymorphicQuery(self.system, self._url, self._object_types, self._query_factory)
        return query.extend_url(*predicates, **kw)


class MonomorphicBinder(BaseBinder): # pylint: disable=abstract-method

    def __init__(self, object_type, system):
        super(MonomorphicBinder, self).__init__(system)
        self.object_type = object_type

    def get_name(self):
        return self.object_type.get_plural_name()

    def __repr__(self):
        return "<{}.{}>".format(self.system, self.get_name())

    @property
    def fields(self):
        return self.object_type.fields

    def is_supported(self):
        return self.object_type.is_supported(self.system)

    def get_url_path(self):
        return self.object_type.get_url_path(self.system)

    def create(self, *args, **kwargs):
        """
        Creates an object on the system
        """
        return self.object_type.create(self.system, *args, **kwargs)

    def get_mutable_fields(self):
        """Returns a list of all mutable fields for this object type
        """
        return [f for f in self.fields if f.mutable]


class TypeBinder(MonomorphicBinder):

    def __init__(self, object_type, system):
        super(TypeBinder, self).__init__(object_type, system)
        self._cache = None

    def is_caching_enabled(self):
        return self._cache is not None

    def find(self, *predicates, **kw):
        """Queries objects according to predicates. Can receive arguments in two possible forms:

        1. Direct keyword arguments, for filtering for equality::

            system.volumes.find(size=GiB)

        2. Complex predicates, using the comparators::

            system.volumes.find(system.volumes.fields.size > GiB)
            system.volumes.find(Q.name != 'some_name')

        :returns: Lazy query result object.

        .. seealso:: :class:`infinisdk.core.object_query.ObjectQuery`
        """
        if self._cache is not None:
            assert not predicates and not kw, "Custom find() is unsupported when forcing queries from cache"
            return self._cache
        query = ObjectQuery(self.system, self.get_url_path(), self.object_type)
        return query.extend_url(*predicates, **kw)

    def get_by_id_lazy(self, id):  # pylint: disable=redefined-builtin
        """
        Obtains an object with a specified id *without* checking if it exists or querying it on the way.

        This is useful assuming the next operation is a further query/update on this object.
        """
        if self._cache is not None:
            obj = self._cache.safe_get_by_id_from_cache(id)
            if obj is not None:
                return obj
        return self.object_type.construct(self.system, {self.fields.id.api_name:id})

    @contextmanager
    def fetch_once_context(self):
        original_cache = self._cache
        try:
            if original_cache is None:
                self._cache = self.get_all()
                for _ in self._cache:
                    pass
            yield
        finally:
            self._cache = original_cache
