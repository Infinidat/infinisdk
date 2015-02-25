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
import arrow
from datetime import timedelta
import munch
from capacity import byte, Capacity
from infi.dtypes.wwn import WWN

from api_object_schema import TypeInfo, ValueTranslator


class CapacityTranslator(ValueTranslator):

    def _to_api(self, value):
        return int(value // byte)

    def _from_api(self, value):
        return int(value) * byte

CapacityType = TypeInfo(type=Capacity, api_type=int,
                        translator=CapacityTranslator())


class MunchTranslator(ValueTranslator):

    def _to_api(self, value):
        if isinstance(value, munch.Munch):
            return value.toDict()
        return value

    def _from_api(self, value):
        return munch.munchify(value)

class MunchListTraslator(ValueTranslator):

    def __init__(self, *args, **kwargs):
        super(MunchListTraslator, self).__init__(*args, **kwargs)
        self._translator = MunchTranslator()

    def _to_api(self, value):
        return [self._translator._to_api(single_value) for single_value in value]

    def _from_api(self, value):
        return [self._translator._from_api(single_value) for single_value in value]

MunchType = TypeInfo(type=munch.Munch, api_type=dict, translator=MunchTranslator())
MunchListType = TypeInfo(type=list, api_type=list, translator=MunchListTraslator())


class MillisecondsDatetimeTranslator(ValueTranslator):

    def _to_api(self, value):
        return int(value.float_timestamp * 1000.0)

    def _from_api(self, value):
        return arrow.get(value / 1000.0)


MillisecondsDatetimeType = TypeInfo(type=arrow.Arrow,
                                    api_type=int, translator=MillisecondsDatetimeTranslator())


class MillisecondsDeltaTranslator(ValueTranslator):

    def _to_api(self, value):
        # for python 2.6 compatibility...
        total_seconds = (value.microseconds + (value.seconds + value.days * 24 * 3600) * 10**6) / 10**6
        return int(total_seconds * 1000.0)

    def _from_api(self, value):
        return timedelta(seconds=int(value), microseconds = int((value - int(value)) * 1000))


MillisecondsDeltaType = TypeInfo(type=arrow.Arrow,
                                  api_type=int, translator=MillisecondsDeltaTranslator())


WWNType = TypeInfo(type=WWN, api_type=str)
