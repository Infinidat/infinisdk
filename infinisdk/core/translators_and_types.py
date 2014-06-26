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
import arrow
from capacity import byte, Capacity

from api_object_schema import TypeInfo, ValueTranslator


class CapacityTranslator(ValueTranslator):

    def _to_api(self, value):
        return int(value // byte)

    def _from_api(self, value):
        return int(value) * byte

CapacityType = TypeInfo(type=Capacity, api_type=int,
                        translator=CapacityTranslator())


class MillisecondsDatetimeTranslator(ValueTranslator):

    def _to_api(self, value):
        return int(value.float_timestamp * 1000)

    def _from_api(self, value):
        return arrow.get(value / 1000.0)

MillisecondsDatetimeType = TypeInfo(type=arrow.Arrow,
                                    api_type=float, translator=MillisecondsDatetimeTranslator())
