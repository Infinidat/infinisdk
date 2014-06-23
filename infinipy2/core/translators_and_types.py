import calendar
import datetime

from capacity import byte, Capacity

from api_object_schema import TypeInfo, ValueTranslator


class CapacityTranslator(ValueTranslator):

    def _to_api(self, value):
        return int(value // byte)

    def _from_api(self, value):
        return int(value) * byte

CapacityType = TypeInfo(type=Capacity, api_type=int,
                        translator=CapacityTranslator())


class DatetimeTranslator(ValueTranslator):

    def _to_api(self, value):
        return calendar.timegm(value.utctimetuple())

    def _from_api(self, value):
        return datetime.datetime.fromtimestamp(value)

DatetimeType = TypeInfo(type=datetime.datetime,
                        api_type=float, translator=DatetimeTranslator())
