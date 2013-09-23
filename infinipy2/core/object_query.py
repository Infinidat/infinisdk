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
        for i in xrange(len(self._fetched)):
            yield self[i]

    def __len__(self):
        self._fetch()
        return self._total_num_objects

    def __getitem__(self, index):
        self._fetch()
        if isinstance(self._fetched[index], dict):
            self._fetched[index] = self.object_type(self.system, self._fetched[index])
        return self._fetched[index]

    def _fetch(self):
        if self._fetched is None:
            response = self.system.api.get(self.query)
            self._fetched = response.get_result()
            self._total_num_objects = response.get_total_num_objects()

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
        translated_fields = [
            self.object_type.fields[field_name].api_name
            for field_name in field_names
        ]
        self.query = add_comma_separated_query_param(self.query, "fields", translated_fields)
        return self
