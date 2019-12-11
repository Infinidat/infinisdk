import copy
import gossip
import functools
import http.client as httplib

from mitba import cached_method
from sentinels import NOTHING
from urlobject import URLObject as URL
from contextlib import contextmanager

from .exceptions import APICommandFailed
from .system_object_utils import get_data_for_object_creation
from .exceptions import CacheMiss
from api_object_schema import FieldsMeta as FieldsMetaBase
from .field import Field
from .type_binder import TypeBinder
from .bindings import PassthroughBinding
from .api.special_values import translate_special_values
from .utils import DONT_CARE, end_reraise_context, add_normalized_query_params
from logbook import Logger

_logger = Logger(__name__)


class FieldsMeta(FieldsMetaBase):

    @classmethod
    def FIELD_FACTORY(mcs, name):  # pylint: disable=bad-mcs-classmethod-argument
        return Field(name, binding=PassthroughBinding())


class BaseSystemObject(metaclass=FieldsMeta):
    """
    Base class for system objects and components
    """

    FIELDS = []
    URL_PATH = None
    UID_FIELD = "id"
    #: specifies which :class:`.TypeBinder` subclass is to be used for this type
    BINDER_CLASS = TypeBinder

    def __init__(self, system, initial_data):
        super(BaseSystemObject, self).__init__()
        #: the system to which this object belongs
        self._system = system
        self._cache = initial_data
        uid_field = self.fields[self.UID_FIELD]
        self._uid = uid_field.binding.get_value_from_api_object(system, type(self), self, self._cache)
        self._use_cache_by_default = False

    @property
    def id(self):
        return self._uid

    @property
    def system(self):
        return self._system

    def get_system(self):
        return self.system

    def invalidate_cache(self, *field_names):
        """Discards the cached field values of this object, causing the next fetch to retrieve the fresh value from
        the system
        """
        if field_names:
            for field_name in field_names:
                self._cache.pop(self.fields.get_or_fabricate(
                    field_name).api_name, None)
        else:
            self._cache.clear()

    @classmethod
    def is_supported(cls, system): # pylint: disable=unused-argument
        return True

    def is_in_system(self):
        """
        Returns whether or not the object actually exists
        """
        try:
            self.get_field(self.UID_FIELD, from_cache=False)
        except APICommandFailed as e:
            if e.status_code != httplib.NOT_FOUND:
                raise
            return False
        else:
            return True

    @staticmethod
    def requires_cache_invalidation(*fields):
        invalidate_fields = fields
        if len(fields) == 1 and callable(fields[0]):
            invalidate_fields = []

        def wraps(func, *args, **kwargs): # pylint: disable=unused-argument
            @functools.wraps(func)
            def invalidates(self, *args, **kwargs):
                returned = func(self, *args, **kwargs)
                self.invalidate_cache(*invalidate_fields)
                return returned
            return invalidates
        if len(fields) == 1 and callable(fields[0]):
            return wraps(fields[0])
        return wraps

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self.get_unique_key() == other.get_unique_key()

    def __ne__(self, other):
        return not (self == other) # pylint: disable=superfluous-parens

    def __hash__(self):
        return hash(self.get_unique_key())

    def get_unique_key(self):
        return (self.system, type(self).__name__, self.id)

    def __deepcopy__(self, memo):
        return self.construct(self.system, copy.deepcopy(self._cache, memo))

    @classmethod
    def construct(cls, system, data):
        """
        Template method to enable customizing the object instantiation process.

        This enables system components to be cached rather than re-fetched every time
        """
        return cls(system, data)

    @classmethod
    def bind(cls, system):
        return cls.BINDER_CLASS(cls, system)

    @classmethod
    def get_type_name(cls):
        return cls.__name__.lower()

    @classmethod
    def get_plural_name(cls):
        return "{}s".format(cls.get_type_name())

    @classmethod
    def get_url_path(cls, system): # pylint: disable=unused-argument
        url_path = cls.URL_PATH
        if url_path is None:
            url_path = "/api/rest/{}".format(cls.get_plural_name())
        return URL(url_path)

    @classmethod
    def get_tags_for_object_operations(cls, system):
        return [cls.get_type_name().lower(), system.get_type_name().lower()]

    def safe_get_field(self, field_name, default=NOTHING, **kwargs):
        """
        Like :meth:`.get_field`, only returns 'default' parameter if no result was found
        """
        try:
            return self.get_field(field_name, **kwargs)
        except CacheMiss:
            return default

    def get_field(self, field_name, from_cache=DONT_CARE, fetch_if_not_cached=True, raw_value=False):
        """
        Gets the value of a single field from the system

        :param cache: Attempt to use the last cached version of the field value
        :param fetch_if_not_cached: Pass ``False`` to force only from cache
        """
        kwargs = {'from_cache': from_cache,
                  'fetch_if_not_cached': fetch_if_not_cached, 'raw_value': raw_value}
        return self.get_fields([field_name], **kwargs)[field_name]

    def get_fields(self, field_names=(), from_cache=DONT_CARE, fetch_if_not_cached=True, raw_value=False):
        """
        Gets a set of fields from the system

        :param from_cache: Attempt to fetch the fields from the cache
        :param fetch_if_not_cached: pass as False to force only from cache
        :returns: a dictionary of field names to their values
        """

        from_cache = self._deduce_from_cache(field_names, from_cache)

        if from_cache:
            if not fetch_if_not_cached:
                return self._get_fields_from_cache(field_names, raw_value)
            field_names_to_retrive = field_names or \
                [field.name for field in self.fields if self.system.is_field_supported(field)]
            try:
                return self._get_fields_from_cache(field_names_to_retrive, raw_value)
            except CacheMiss:
                pass

        query = self.get_this_url_path()

        only_fields = []
        for field_name in field_names:
            try:
                only_fields.append(
                    self._get_field_api_name_if_defined(field_name))
            except LookupError:
                only_fields.append(field_name)

        if only_fields:
            query = query.add_query_param("fields", ",".join(only_fields))

        response = self.system.api.get(query)

        result = response.get_result()
        self.update_field_cache(result)

        if not field_names:
            field_names = self.fields.get_all_field_names_or_fabricate(result)

        return self._get_fields_from_cache(field_names, raw_value)

    def _is_caching_enabled(self):
        return self.system.is_caching_enabled()

    def _deduce_from_cache(self, field_names, from_cache):
        if from_cache is not DONT_CARE:
            return from_cache

        if not field_names:
            return False

        if self._use_cache_by_default:
            return True

        cache_enabled = self._is_caching_enabled()
        for field_name in field_names:
            field = self.fields.get_or_fabricate(field_name)
            should_get_from_cache = field.cached
            if should_get_from_cache is DONT_CARE:
                should_get_from_cache = cache_enabled

            if not should_get_from_cache:
                return False

        return True

    def _get_field_api_name_if_defined(self, field_name):
        field = self.fields.get(field_name, None)
        if field is None:
            return field_name
        return field.api_name

    def _get_fields_from_cache(self, field_names, raw_value):
        if not field_names:
            field_names = self.fields.get_all_field_names_or_fabricate(
                self._cache.keys())
        returned = {}
        missed = []
        for field_name in field_names:
            field = self.fields.get_or_fabricate(field_name)
            try:
                if raw_value:
                    value = self._cache[field.api_name]
                else:
                    value = field.binding.get_value_from_api_object(
                        self.system, type(self), self, self._cache)
            except KeyError:
                if self.system.is_field_supported(field):
                    missed.append(field_name)
            else:
                returned[field_name] = value
        if missed:
            raise CacheMiss(
                "The following fields could not be obtained from cache: {}".format(
                    ", ".join(repr(field) for field in missed)))

        return returned

    def is_field_supported(self, field_name):
        field = self.fields.get_or_fabricate(field_name)
        return self.system.is_field_supported(field)

    def update_field_cache(self, api_obj):
        assert all(isinstance(key, (str, bytes)) for key in api_obj.keys())
        self._cache.update(api_obj)

    def update_field(self, field_name, field_value):
        """
        Updates the value of a single field
        """
        self._update_fields({field_name: field_value})

    def update_fields(self, **update_dict):
        """Atomically updates a group of fields and respective values (given as a dictionary)
        """
        self._update_fields(update_dict)

    def _update_fields(self, update_dict):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags(
            'infinidat.sdk.pre_fields_update',
            {'source': self, 'fields': update_dict}, tags=hook_tags)

        for field_name, field_value in list(update_dict.items()):
            try:
                field = self.fields[field_name]
            except LookupError:
                continue
            translated_value = field.binding.get_api_value_from_value(
                self.system, type(self), self, field_value)
            update_dict[field.api_name] = translated_value
            if field.api_name != field_name:
                update_dict.pop(field_name)

        gossip.trigger_with_tags('infinidat.sdk.pre_object_update', {'obj': self, 'data': update_dict},
                                 tags=hook_tags)
        try:
            res = self.system.api.put(self.get_this_url_path(), data=update_dict)
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.object_update_failure',
                                         {'obj': self, 'exception': e, 'system': self.system, 'data': update_dict},
                                         tags=hook_tags)
        response_dict = res.get_result()
        if len(update_dict) == 1 and not isinstance(response_dict, dict):
            [key] = update_dict.keys()
            response_dict = {key: response_dict}
        self.update_field_cache({k: response_dict[k] for k in update_dict if k in response_dict})
        gossip.trigger_with_tags('infinidat.sdk.post_object_update',
                                 {'obj': self, 'data': update_dict, 'response_dict': response_dict}, tags=hook_tags)
        return res

    @cached_method
    def get_this_url_path(self):
        return URL(self.get_url_path(self.system)).add_path(str(self.id))

    def __repr__(self):
        id_string = 'id={}'.format(self.id)
        for field in self.FIELDS:
            if field.use_in_repr:
                try:
                    value = self.get_field(
                        field.name, from_cache=True, fetch_if_not_cached=False)
                except CacheMiss:
                    value = '?'
                id_string += ', {}={}'.format(field.name, value)

        return "<{system_name}:{typename} {id_string}>".format(
            typename=type(self).__name__,
            system_name=self.system.get_name(),
            id_string=id_string)


class SystemObject(BaseSystemObject):
    """
    System object, that has query methods, creation and deletion
    """

    @classmethod
    def find(cls, system, *predicates, **kw):
        binder = system.objects[cls.get_plural_name()]
        return binder.find(*predicates, **kw)

    def get_binder(self):
        return self.system.objects[self.get_plural_name()]

    def get_collection(self):
        return self.get_binder()

    def _is_caching_enabled(self):
        return self.get_binder().is_caching_enabled() or super(SystemObject, self)._is_caching_enabled()

    @classmethod
    def _create(cls, system, url, data, tags=None, parent=None):
        hook_tags = tags or cls.get_tags_for_object_operations(system)
        gossip.trigger_with_tags('infinidat.sdk.pre_object_creation',
                                 {'data': data, 'system': system, 'cls': cls, 'parent': parent},
                                 tags=hook_tags)
        try:
            returned = system.api.post(url, data=data).get_result()
            obj = cls(system, returned)
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.object_creation_failure',
                                         {'cls': cls, 'system': system, 'data': data, 'parent': parent, 'exception': e},
                                         tags=hook_tags)
        gossip.trigger_with_tags('infinidat.sdk.post_object_creation',
                                 {'obj': obj, 'data': data, 'response_dict': returned, 'parent': parent},
                                 tags=hook_tags)
        return obj

    @classmethod
    def create(cls, system, **fields):
        """
        Creates a new object of this type
        """
        hook_tags = cls.get_tags_for_object_operations(system)
        gossip.trigger_with_tags('infinidat.sdk.pre_creation_data_validation',
                                 {'fields': fields, 'system': system, 'cls': cls},
                                 tags=hook_tags)
        data = get_data_for_object_creation(cls, system, fields)
        return cls._create(system, cls.get_url_path(system), data)

    @classmethod
    def get_creation_defaults(cls):
        """
        Returns a dict representing the default arguments as implicitly constructed by infinisdk to fulfill
        a ``create`` call

        .. note:: This will cause generation of defaults, which will have side effects if they are special values

        .. note:: This does not necessarily generate all fields that are passable into ``create``, only mandatory
          'fields
        """
        return translate_special_values(dict(
            (field.name, field.generate_default())
            for field in cls.fields  # pylint: disable=no-member
            if field.creation_parameter and not field.optional))

    @contextmanager
    def using_cache_by_default(self):
        prev_value = self._use_cache_by_default
        self._use_cache_by_default = True
        _logger.debug('Entered use cache by default context for object {}', self)
        try:
            yield
        finally:
            self._use_cache_by_default = prev_value
            _logger.debug('Exited use cache by default for object {}, use_cache new value is {}', self, prev_value)


    def safe_delete(self, *args, **kwargs):
        """
        Tries to delete the object, doing nothing if the object cannot be found on the system
        """
        try:
            self.delete(*args, **kwargs)
        except APICommandFailed as e:
            if e.status_code != httplib.NOT_FOUND:
                raise

    def delete(self, **kwargs):
        """
        Deletes this object.
        """
        self._send_delete_with_hooks_tirggering(self.get_this_url_path(), **kwargs)

    def _send_delete_with_hooks_tirggering(self, url, **kwargs):
        url = add_normalized_query_params(url, **kwargs)
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.pre_object_deletion', {'obj': self, 'url': url}, tags=hook_tags)
        try:
            resp = self.system.api.delete(url)
            self._use_cache_by_default = True
        except Exception as e:       # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.object_deletion_failure',
                                         {'obj': self, 'exception': e, 'system': self.system, 'url': url},
                                         tags=hook_tags)
        result = resp.get_result()
        if isinstance(result, dict):
            self.update_field_cache(result)
        gossip.trigger_with_tags('infinidat.sdk.post_object_deletion', {'obj': self, 'url': url}, tags=hook_tags)
        return resp


@gossip.register('infinidat.sdk.object_creation_failure')
@gossip.register('infinidat.sdk.object_deletion_failure')
@gossip.register('infinidat.sdk.object_update_failure')
def _notify_operation_failed(system, exception, **kwargs):
    cls = kwargs.pop('cls', None) or type(kwargs.pop('obj'))
    tags = cls.get_tags_for_object_operations(system)
    gossip.trigger_with_tags('infinidat.sdk.object_operation_failure', {'exception': exception}, tags=tags)
