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
