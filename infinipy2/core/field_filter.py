class FieldFilter(object):

    def __init__(self, field, operator_name, value):
        super(FieldFilter, self).__init__()
        self.field = field
        self.operator_name = operator_name
        self.value = value

    def add_to_url(self, urlobj):
        return urlobj.add_query_param(self.field.api_name, "{0}:{1}".format(
            self.operator_name,
            self.field.translator.to_api(self.value)))

