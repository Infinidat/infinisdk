from api_object_schema import TypeInfo
from api_object_schema import ValueTranslator
from capacity import byte, Capacity


class CapacityTranslator(ValueTranslator):
    def _to_api(self, value):
        return int(value // byte)

    def _from_api(self, value):
        return int(value) * byte

CapacityType = TypeInfo(type=Capacity, api_type=int, translator=CapacityTranslator())
