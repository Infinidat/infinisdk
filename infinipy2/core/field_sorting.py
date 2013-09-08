class FieldSorting(object):

    def __init__(self, field, prefix=""):
        super(FieldSorting, self).__init__()
        self.field = field
        self.prefix = prefix

    def add_to_url(self, url):
        existing_sort = url.query_dict.get("sort", "")
        if existing_sort:
            existing_sort = "{0},".format(existing_sort)

        return url.set_query_param("sort", "{0}{1}{2}".format(existing_sort, self.prefix, self.field.api_name))
