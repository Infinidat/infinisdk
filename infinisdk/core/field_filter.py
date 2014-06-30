###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
class FieldFilter(object):

    def __init__(self, field, operator_name, value):
        super(FieldFilter, self).__init__()
        self.field = field
        self.operator_name = operator_name
        self.value = value

    def _translate(self, value):
        return self.field.binding.get_api_value_from_value(None, None, None, value)

    def add_to_url(self, urlobj):
        if isinstance(self.value, (list, tuple)):
            value = "({0})".format(",".join(str(self._translate(val))
                                            for val in self.value))
        else:
            value = self._translate(self.value)

        return urlobj.add_query_param(self.field.api_name,
                                      "{0}:{1}".format(self.operator_name,
                                                       value))
