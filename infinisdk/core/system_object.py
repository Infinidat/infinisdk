import itertools
import gossip
from contextlib import contextmanager
from sentinels import NOTHING, Sentinel
from infi.pyutils.lazy import cached_method
from urlobject import URLObject as URL

from .exceptions import APICommandFailed, ObjectNotFound
from .._compat import with_metaclass, iteritems, itervalues, httplib
from .exceptions import MissingFields, CacheMiss
from api_object_schema import FieldsMeta as FieldsMetaBase
from .field import Field
from .object_query import ObjectQuery
from .type_binder import TypeBinder
from .api.special_values import translate_special_values

DONT_CARE = Sentinel("DONT_CARE")

def _install_gossip_hooks():
    for (hook, operation) in itertools.product(["pre", "post"], ['creation', 'deletion', 'update']):
        gossip.define("infinidat.{0}_object_{1}".format(hook, operation))
    gossip.define("infinidat.object_operation_failure")

_install_gossip_hooks()

class FieldsMeta(FieldsMetaBase):

    FIELD_FACTORY = Field

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
        self.id = self.fields.id.extract_from_json(self, self._cache)

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented

        return self.system == other.system and self.id == other.id

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.system, type(self), self.id))

    @classmethod
    def construct(cls, system, data):
        """
        Template method to enable customizing the object instantiation process.

        This enables system components to be cached rather than re-fetched every time
        """
        return cls(system, data)

    def is_in_system(self):
        """
        Returns whether or not the object actually exists
        """
        try:
            self.get_field("id", from_cache=False)
        except APICommandFailed as e:
            if e.status_code != httplib.NOT_FOUND:
                raise
            return False
        else:
            return True

    @classmethod
    def create(cls, system, **fields):
        data = cls._get_data_for_post(fields)
        gossip.trigger('infinidat.pre_object_creation', data=data, system=system, cls=cls)
        with _possible_api_failure_context():
            returned = cls(system, system.api.post(cls.get_url_path(system), data=data).get_result())
        gossip.trigger('infinidat.post_object_creation', obj=returned, data=data)
        return returned

    @classmethod
    def _get_data_for_post(cls, fields):
        returned = {}
        missing_fields = set()
        extra_fields = fields.copy()
        for field in cls.fields:
            if field.name not in fields:
                if not field.creation_parameter or field.optional:
                    continue

            field_value = extra_fields.get(field.name, NOTHING)
            extra_fields.pop(field.name, None)
            field_api_value = extra_fields.get(field.api_name, NOTHING)
            extra_fields.pop(field.api_name, None)
            if field_value is NOTHING and field_api_value is NOTHING:
                field_value = field.generate_default()
            if field_value is not NOTHING and field_api_value is not NOTHING:
                raise ValueError("Multiple colliding arguments: {0} and {1}".format(field.name, field.api_name))
            if field_value is NOTHING and field_api_value is NOTHING:
                missing_fields.add(field.name)
            if field_value is not NOTHING:
                returned[field.api_name] = field.binding.get_raw_api_value(field.type.translator.to_api(field_value))
            else:
                returned[field.api_name] = field_api_value
        if missing_fields:
            raise MissingFields("Following fields were not specified: {0}".format(", ".join(sorted(missing_fields))))
        returned.update(extra_fields)
        return returned

    @classmethod
    def bind(cls, system):
        return cls.BINDER_CLASS(cls, system)

    @classmethod
    def get_type_name(cls):
        return cls.__name__.lower()

    @classmethod
    def get_plural_name(cls):
        return cls.get_type_name() + "s"

    @classmethod
    def get_creation_defaults(cls):
        """
        Returns a dict representing the default arguments as implicitly constructed by infinisdk to fulfill a ``create`` call

        .. note:: this will cause generation of defaults, which will have side effects if they are special values

        .. note:: this does not necessarily generate all fields that are passable into ``create``, only mandatory fields
        """
        return translate_special_values(dict(
            (field.name, field.generate_default())
            for field in cls.fields
            if field.creation_parameter and not field.optional))

    @classmethod
    def get_url_path(cls, system):
        url_path = cls.URL_PATH
        if url_path is None:
            url_path = "/api/rest/{0}".format(cls.get_plural_name())
        return url_path

    @classmethod
    def find(cls, system, *predicates, **kw):
        url = URL(cls.get_url_path(system))
        if kw:
            predicates = itertools.chain(
                predicates,
                (cls.fields.get_or_fabricate(key) == value for key, value in iteritems(kw)))
        for pred in predicates:
            url = pred.add_to_url(url)

        return ObjectQuery(system, url, cls)

    def get_field(self, field_name, from_cache=DONT_CARE, fetch_if_not_cached=True):
        """
        Gets the value of a single field from the system

        :param cache: Attempt to use the last cached version of the field value
        :param fetch_if_not_cached: pass as False to force only from cache
        """
        return self.get_fields([field_name], from_cache=from_cache, fetch_if_not_cached=fetch_if_not_cached)[field_name]

    def get_fields(self, field_names=(), from_cache=DONT_CARE, fetch_if_not_cached=True):
        """
        Gets a set of fields from the system

        :param from_cache: Attempt to fetch the fields from the cache
        :param fetch_if_not_cached: pass as False to force only from cache
        :rtype: a dictionary of field names to their values
        """

        from_cache = self._deduce_from_cache(field_names, from_cache)

        if from_cache:
            try:
                return self._get_fields_from_cache(field_names)
            except CacheMiss:
                if not fetch_if_not_cached:
                    raise

        # TODO: remove unnecessary construction, move to direct getting
        query = self.get_this_url_path()

        only_fields = []
        for field_name in field_names:
            try:
                only_fields.append(self._get_field_api_name_if_defined(field_name))
            except LookupError:
                only_fields.append(field_name)

        if only_fields:
            query = query.add_query_param("fields", ",".join(only_fields))

        response = self.system.api.get(query)

        result = response.get_result()
        self.update_field_cache(result)

        if not field_names:
            field_names = self.fields.get_all_field_names_or_fabricate(result)

        returned = {}
        for field_name in field_names:
            field = self.fields.get(field_name, None)
            if field is not None:
                #value = field.type.translator.from_api(field.extract_from_json(self, self._cache))
                value = field.type.translator.from_api(self._cache[field.api_name])
            else:
                value = self._cache[field_name]
            returned[field_name] = value

        return returned

    def _deduce_from_cache(self, field_names, from_cache):
        if from_cache is not DONT_CARE:
            return from_cache


        if not field_names:
            return False

        for field_name in field_names:
            field = self.fields.get_or_fabricate(field_name)
            if not field.cached and not field.is_identity:
                return False
        return True

    def _get_field_api_name_if_defined(self, field_name):
        field = self.fields.get(field_name, None)
        if field is None:
            return field_name
        return field.api_name

    def _get_fields_from_cache(self, field_names):
        returned = {}
        missed = []
        for field_name in field_names:
            value = self._cache.get(self._get_field_api_name_if_defined(field_name), NOTHING)
            if value is NOTHING:
                missed.append(field_name)
            else:
                returned[field_name] = value
        if missed:
            raise CacheMiss(
                "The following fields could not be obtained from cache: {0}".format(
                    ", ".join(repr(field) for field in missed)))

        return returned

    def update_field_cache(self, api_obj):
        self._cache.update(api_obj)

    def update_field(self, field_name, field_value):
        """
        Updates the value of a single field
        """
        self._update_fields({field_name: field_value})

    def update_fields(self, **update_dict):
        """
        Atomically update a group of fields and respective values (given as a dictionary)
        """
        self._update_fields(update_dict)

    def _update_fields(self, update_dict):
        for field_name, field_value in list(iteritems(update_dict)):
            try:
                field = self.fields[field_name]
            except LookupError:
                continue
            update_dict[field.api_name] = field.type.translator.to_api(field_value)
            if field.api_name != field_name:
                update_dict.pop(field_name)

        self.system.api.put(self.get_this_url_path(), data=update_dict)

    def delete(self):
        """
        Deletes this object.

        .. note:: does nothing except sending the deletion request. See :func:`.purge` for forcibly deleting objects.
        """
        self.system.api.delete(self.get_this_url_path())

    def purge(self):
        """
        Deletes this object, doing all necessary operations to ensure deletion is successful.
        """
        self.delete()

    @cached_method
    def get_this_url_path(self):
        return URL(self.get_url_path(self.system)).add_path(str(self.id))

    def __repr__(self):
        return "<{0} id={1}>".format(type(self).__name__, self.id)

@contextmanager
def _possible_api_failure_context():
    try:
        yield
    except APICommandFailed as e:
        gossip.trigger('infinidat.object_operation_failure')
        raise
