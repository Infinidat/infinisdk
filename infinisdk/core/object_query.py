import itertools
import random
from urlobject import URLObject as URL
from numbers import Number
from .field import Field
from .field_filter import FieldFilter
from .q import QField
from .exceptions import ObjectNotFound, ChangedDuringIteration

_DEFAULT_SYSTEM_PAGE_SIZE = 50
_DEFAULT_PAGE_SIZE = 1000


class QueryBase:

    def count(self):
        return len(self)

    def __nonzero__(self):
        return len(self) != 0

    __bool__ = __nonzero__

    def to_list(self):
        """Returns the entire set of objects as a Python list

        .. caution:: Queries are lazy by default to avoid heavy API calls and repetitive page
          requests. Using ``to_list`` will forcibly iterate and fetch all objects, which might
          be a very big collection. This can cause issues like slowness and memory exhaustion
        """
        return list(self)

    def choose(self):
        try:
            return self.sample(1)[0]
        except ValueError:
            raise ObjectNotFound('No items where returned')

    def sample(self, sample_count):
        """
        Chooses a random sample out of the query's objects.
        Raises ValueError if there are not enough items
        """
        if sample_count <= 0:
            raise ValueError('Illegal sample size ({})'.format(sample_count))
        query_size = self.count()
        if query_size < sample_count:
            raise ValueError('Sample larger than returned items ({} > {})'.format(sample_count, query_size))
        indexes = random.sample(range(query_size), sample_count)
        return [self[index] for index in indexes]

class LazyQuery(QueryBase):
    def __init__(self, system, url, factory=None):
        super(LazyQuery, self).__init__()
        self.factory = factory
        self.system = system
        self.query = url
        self._requested_page = None
        self._requested_page_size = None
        self._fetched = {}
        self._objects_by_id = {}
        self._total_num_objects = None
        self._mutable = True

    def safe_get_by_id_from_cache(self, id): # pylint: disable=redefined-builtin
        return self._objects_by_id.get(id)

    def extend_url(self, *args, **kw):
        assert self._mutable, "Cannot modify query after fetching"
        if args:
            raise NotImplementedError("Positional arguments are not supported for LazyQuery")
        url = URL(self.query)
        if kw:
            url = url.add_query_params(**kw)
        self.query = url
        return self

    def __iter__(self):
        if self._total_num_objects is None:
            self._fetch()
        if self._requested_page is not None:
            start = (self._requested_page - 1) * self._requested_page_size
            end = min(start + self._requested_page_size, len(self))
        else:
            start = 0
            end = len(self)
        for i in range(start, end):
            try:
                yield self[i]
            except IndexError:
                if i != self._total_num_objects:
                    raise ChangedDuringIteration("Queried path's size changed during iteration")

    def __len__(self):
        if self._total_num_objects is None:
            self._fetch()
        if self._requested_page is None:
            return self._total_num_objects
        return self._get_requested_page_size()

    def _get_requested_page_size(self):
        if self._total_num_objects >= self._requested_page * self._requested_page_size:
            return self._requested_page_size
        return self._total_num_objects % self._requested_page_size

    def _translate_item_if_needed(self, item_index):
        if self.factory is None:
            return

        received_item = self._fetched.get(item_index)
        if isinstance(received_item, dict):
            obj = self._fetched[item_index] = self.factory(self.system, received_item)
            self._objects_by_id[obj.id] = obj

    def __getitem__(self, index):
        if isinstance(index, Number) and index < 0:
            raise NotImplementedError("Negative indices not supported yet")

        self._fetch(index)
        self._translate_item_if_needed(index)
        try:
            return self._fetched[index]
        except LookupError:
            raise IndexError()

    def _fetch(self, element_index=None):
        self._mutable = False
        element_index = self._get_requested_element_index(element_index)
        assert element_index is not None
        if self._fetched.get(element_index) is None:
            query = self._get_query_for_index(element_index)
            response = self.system.api.get(query)

            if self._total_num_objects is None:
                self._total_num_objects = response.get_total_num_objects()

            for index, obj in enumerate(response.get_result(), start=response.get_page_start_index()):
                if self._fetched.get(index) is None:
                    self._fetched[index] = obj

    def _get_query_for_index(self, element_index):
        returned = self.query
        if self._requested_page_size is None and element_index < _DEFAULT_SYSTEM_PAGE_SIZE:
            return returned
        page_size = self._requested_page_size if self._requested_page_size is not None else _DEFAULT_PAGE_SIZE
        page_number = int(element_index // page_size) + 1
        returned = returned.set_query_param("page", str(page_number))\
                           .set_query_param("page_size", str(page_size))
        return returned

    def _get_requested_element_index(self, element_index):
        if element_index is None:
            if self._requested_page is not None:
                element_index = (self._requested_page - 1) * self._requested_page_size
            else:
                element_index = 0
        return element_index

    def __str__(self):
        return str(self.query)

    def __repr__(self):
        return "<Query {}>".format(self)

    def page(self, page_index):
        """
        Requests a specific pagination page
        """
        assert page_index != 0, "Page cannot be zero based"
        assert self._mutable, "Cannot modify query after fetching"
        self._requested_page = page_index
        return self

    def page_size(self, page_size):
        """
        Sets the page size of the query
        """
        assert self._mutable, "Cannot modify query after fetching"
        self._requested_page_size = page_size
        return self


class PolymorphicQuery(LazyQuery):
    def __init__(self, system, url, object_types, factory):
        super(PolymorphicQuery, self).__init__(system, url, factory)
        assert isinstance(object_types, (list, tuple)), "object_types must be tuple or list"
        self.object_types = object_types
        assert callable(self.factory), "A callable factory must be provided for PolymorphicQuery"

    def _get_or_fabricate_field(self, field_name):
        for obj_type in self.object_types:
            field = obj_type.fields.get(field_name)
            if field is not None:
                return field
        return self.object_types[0].fields.get_or_fabricate(field_name)

    def extend_url(self, *predicates, **kw):
        assert self._mutable, "Cannot modify query after fetching"
        url = URL(self.query)
        if kw:
            predicates = itertools.chain(predicates, (self._get_or_fabricate_field(key) == value
                                                      for key, value in kw.items()))

        for pred in predicates:
            if isinstance(pred.field, QField):
                pred = FieldFilter(self._get_or_fabricate_field(pred.field.name), pred.operator_name, pred.value)
            url = pred.add_to_url(url, self.system)
        self.query = url
        return self

    ### Modifiers

    def sort(self, *criteria):
        """
        Sorts the response according to the specified fields criteria
        """
        assert self._mutable, "Cannot modify query after fetching"
        query = self.query
        for c in criteria:
            if isinstance(c, Field):
                c = +c
            query = c.add_to_url(query)
        self.query = query
        return self

    def only_fields(self, field_names):
        """
        Plucks the specified field names from the query. Can be specified multiple times
        """
        assert isinstance(field_names, (list, tuple)), "field_names must be either a list or a tuple"
        assert self._mutable, "Cannot modify query after fetching"
        query_fields = self.query.query_dict.get("fields", None)
        requested_fields = set([] if not query_fields else query_fields.split(","))

        for object_type in self.object_types:
            for field_name in field_names:
                requested_fields.add(object_type.fields[field_name].api_name)

        for object_type in self.object_types:
            for field in object_type.fields.get_identity_fields():
                if field.api_name not in requested_fields:
                    requested_fields.add(field.api_name)
            self.query = self.query.set_query_param("fields", ",".join(requested_fields))
        return self


class ObjectQuery(PolymorphicQuery):
    def __init__(self, system, url, object_type):
        super(ObjectQuery, self).__init__(system, url, (object_type, ), object_type.construct)
        self.object_type = object_type

    def _get_or_fabricate_field(self, field_name):
        return self.object_type.fields.get_or_fabricate(field_name)
