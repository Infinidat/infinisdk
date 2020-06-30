from .utils import add_comma_separated_query_param

class FieldSorting:

    def __init__(self, field, prefix=""):
        super(FieldSorting, self).__init__()
        self.field = field
        self.prefix = prefix

    def add_to_url(self, url):
        return add_comma_separated_query_param(url, "sort", self.prefix + self.field.api_name)
