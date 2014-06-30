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
from api_object_schema import ObjectAPIBinding

from .api.special_values import SpecialValue


class InfiniSDKBinding(ObjectAPIBinding):

    def get_api_value_from_value(self, system, objtype, obj, value):
        if isinstance(value, SpecialValue):
            return value
        return super(InfiniSDKBinding, self).get_api_value_from_value(system, objtype, obj, value)

class RelatedObjectBinding(InfiniSDKBinding):

    def __init__(self, collection_name=None, value_for_none=0):
        super(RelatedObjectBinding, self).__init__()
        self._collection_name = collection_name
        self._value_for_none = value_for_none

    def set_field(self, field):
        super(RelatedObjectBinding, self).set_field(field)
        if not self._collection_name:
            self._collection_name = "{0}s".format(field.name)

    def get_api_value_from_value(self, system, objtype, obj, value):
        if value is None:
            return self._value_for_none
        return value.id

    def get_value_from_api_value(self, system, objtype, obj, value):
        if value == self._value_for_none:
            return None
        return getattr(system, self._collection_name).get_by_id_lazy(value)


class PassthroughBinding(InfiniSDKBinding):

    def get_api_value_from_value(self, system, objtype, obj, value):
        return value

    def get_value_from_api_value(self, system, objtype, obj, value):
        return value
