from .._compat import xrange
from .utils import add_comma_separated_query_param
from .field import Field

class ObjectQuery(object):
    def __init__(self, system, url, object_type):
        super(ObjectQuery, self).__init__()
        self.system = system
        self.query = url
        self.object_type = object_type
        self._fetched = None
        self._total_num_objects = None

    def __iter__(self):
        self._fetch()
        for i in xrange(len(self)):
            yield self[i]

    def __len__(self):
        self._fetch()
        return self._total_num_objects

    def __getitem__(self, index):
        self._fetch(index)
        if isinstance(self._fetched[index], dict):
            self._fetched[index] = self.object_type.construct(self.system, self._fetched[index])
        return self._fetched[index]

    def _fetch(self, element_index=0):
        if self._total_num_objects is not None and element_index >= self._total_num_objects:
            raise IndexError()
        if self._fetched is None or element_index >= len(self._fetched) or self._fetched[element_index] is None:
            query = self.query
            page_size = query.query_dict.get("page_size")
            page_index = query.query_dict.get("page")
            if page_size is not None and page_index is not None:
                page_size = int(page_size)
                page_index = int(element_index // int(page_size)) + 1
                query = query.set_query_param("page", str(page_index))
                starting_offset = page_size * (page_index - 1)
            else:
                starting_offset = 0

            response = self.system.api.get(query)

            if self._total_num_objects is None:
                self._total_num_objects = response.get_total_num_objects()

            if self._fetched is None:
                self._fetched = [None for i in xrange(self._total_num_objects)]

            for index, obj in enumerate(response.get_result(), start=starting_offset):
                if self._fetched[index] is None:
                    self._fetched[index] = obj



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
        self.query = self.query.set_query_param("page", str(page_index))
        return self

    def page_size(self, page_size):
        """
        Sets the page size of the query
        """
        self.query = self.query.set_query_param("page_size", str(page_size))
        if "page" not in self.query.query_dict:
            self.page(1)
        return self
