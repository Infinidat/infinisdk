###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from .utils import add_comma_separated_query_param

class FieldSorting(object):

    def __init__(self, field, prefix=""):
        super(FieldSorting, self).__init__()
        self.field = field
        self.prefix = prefix

    def add_to_url(self, url):
        return add_comma_separated_query_param(url, "sort", self.prefix + self.field.api_name)
