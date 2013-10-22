from .._compat import xrange
from .utils import add_comma_separated_query_param
from .field import Field

class ObjectQuery(object):
    def __init__(self, system, url, object_type):
        super(ObjectQuery, self).__init__()
        self.system = system
        self.query = url
        self.object_type = object_type
        self._requested_page = None
        self._requested_page_size = None
        self._fetched = None
        self._total_num_objects = None

    def __iter__(self):
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
                pass

    def __len__(self):
        self._fetch()
        if self._requested_page is None:
            return self._total_num_objects
        return self._get_requested_page_size()

    def _get_requested_page_size(self):
        if self._total_num_objects >= self._requested_page * self._requested_page_size:
            return self._requested_page_size
        return self._total_num_objects % self._requested_page_size

    def __getitem__(self, index):
        self._fetch(index)
        if isinstance(self._fetched[index], dict):
            self._fetched[index] = self.object_type.construct(self.system, self._fetched[index])
        return self._fetched[index]

    def _fetch(self, element_index=None):
        element_index = self._get_requested_element_index(element_index)
        assert element_index is not None
        if self._total_num_objects is not None and element_index >= self._total_num_objects:
            raise IndexError()
        if self._fetched is None or element_index >= len(self._fetched) or self._fetched[element_index] is None:
            query = self._get_query_for_index(element_index)
            response = self.system.api.get(query)

            if self._total_num_objects is None:
                self._total_num_objects = response.get_total_num_objects()

            if self._fetched is None:
                self._fetched = [None for i in xrange(self._total_num_objects)]

            for index, obj in enumerate(response.get_result(), start=response.get_page_start_index()):
                if self._fetched[index] is None:
                    self._fetched[index] = obj

    def _get_query_for_index(self, element_index):
        returned = self.query
        if self._requested_page_size is None:
            return returned
        page_number = int(element_index // self._requested_page_size) + 1
        returned = returned.set_query_param("page", str(page_number))\
                           .set_query_param("page_size", str(self._requested_page_size))
        return returned

    def _get_requested_element_index(self, element_index):
        if element_index is None:
            if self._requested_page is not None:
                element_index = (self._requested_page - 1) * self._requested_page_size
            else:
                element_index = 0
        return element_index


    def __repr__(self):
        return "<Query {}>".format(self.query)

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
        translated_fields = [
            self.object_type.fields[field_name].api_name
            for field_name in field_names
        ]
        self.query = add_comma_separated_query_param(self.query, "fields", translated_fields)
        fields = self.query.query_dict["fields"].split(",")
        # make sure we pluck the 'id' field
        if self.object_type.fields.id.api_name not in fields:
            fields.insert(0, self.object_type.fields.id.api_name)
            self.query = self.query.set_query_param("fields", ",".join(fields))
        return self

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
