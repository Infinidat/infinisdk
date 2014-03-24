class FieldFilter(object):

    def __init__(self, field, operator_name, value):
        super(FieldFilter, self).__init__()
        self.field = field
        self.operator_name = operator_name
        self.value = value

    def add_to_url(self, urlobj):
        translate = self.field.type.translator.to_api

        if isinstance(self.value, (list, tuple)):
            value = "({0})".format(",".join(str(translate(val))
                                            for val in self.value))
        else:
            value = translate(self.value)

        return urlobj.add_query_param(self.field.api_name,
                                      "{0}:{1}".format(self.operator_name,
                                                       value))

