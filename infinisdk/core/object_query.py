from numbers import Number
from .._compat import xrange
from .field import Field

_DEFAULT_SYSTEM_PAGE_SIZE = 50
_DEFAULT_PAGE_SIZE = 1000


class LazyQuery(object):
    def __init__(self, system, url):
        super(LazyQuery, self).__init__()
        self.system = system
        self.query = url
        self._requested_page = None
        self._requested_page_size = None
        self._fetched = {}
        self._total_num_objects = None

    def __iter__(self):
        if self._total_num_objects is None:
            self._fetch()
        if self._requested_page is not None:
            start = (self._requested_page - 1) * self._requested_page_size
            end = start + self._requested_page_size
        else:
            start = 0
            end = len(self)
        for i in xrange(start, end):
            try:
                yield self[i]
            except IndexError:
                if i != self._total_num_objects:
                    raise

    def __len__(self):
        if self._total_num_objects is None:
            self._fetch()
        if self._requested_page is None:
            return self._total_num_objects
        return self._get_requested_page_size()

    def __nonzero__(self):
        return len(self) != 0

    __bool__ = __nonzero__

    def _get_requested_page_size(self):
        if self._total_num_objects >= self._requested_page * self._requested_page_size:
            return self._requested_page_size
        return self._total_num_objects % self._requested_page_size

    def _translate_item_if_needed(self, item_index):
        pass

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


    def __repr__(self):
        return "<Query {0}>".format(self.query)

    def page(self, page_index):
        """
        Requests a specific pagination page
        """
        assert page_index != 0, "Page cannot be zero based"
        self._requested_page = page_index
        return self

    def page_size(self, page_size):
        """
        Sets the page size of the query
        """
        self._requested_page_size = page_size
        return self

    def to_list(self):
        """Returns the entire set of objects as a Python list

        .. caution:: Queries are lazy by default to avoid heavy API calls and repetitive page
          requests. Using ``to_list`` will forcibly iterate and fetch all objects, which might
          be a very big collection. This can cause issues like slowness and memory exhaustion
        """
        return list(self)


class ObjectQuery(LazyQuery):

    def __init__(self, system, url, object_type):
        self.object_type = object_type
        super(ObjectQuery, self).__init__(system, url)

    def _translate_item_if_needed(self, item_index):
        received_item = self._fetched.get(item_index)
        if isinstance(received_item, dict):
            self._fetched[item_index] = self.object_type.construct(self.system, received_item)


    ### Modifiers

    def sort(self, *criteria):
        """
        Sorts the response according to the specified fields criteria
        """
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
        requested_fields = [
        ]
        requested_fields = self.query.query_dict.get("fields", None)
        if requested_fields is not None:
            requested_fields = requested_fields.split(",")
        else:
            requested_fields = []
        requested_fields.extend(
            self.object_type.fields[field_name].api_name
            for field_name in field_names
            )

        for field in self.object_type.fields.get_identity_fields():
            if field.api_name not in requested_fields:
                requested_fields.insert(0, field.api_name)
        self.query = self.query.set_query_param("fields", ",".join(requested_fields))
        return self
