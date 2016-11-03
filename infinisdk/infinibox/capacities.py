
from capacity import Capacity
from mitba import cached_method
from urlobject import URLObject as URL
from api_object_schema.binding import ConstBinding
from api_object_schema import TypeInfo
from ..core.system_object import SystemObject
from ..core.field import Field
from ..core.exceptions import CapacityUnavailable
from ..core.translators_and_types import CapacityTranslator

class SystemCapacityTranslator(CapacityTranslator):
    def _from_api(self, value):
        if value is None:
            raise CapacityUnavailable()
        return super(SystemCapacityTranslator, self)._from_api(value)

SystemCapacityType = TypeInfo(type=Capacity, api_type=int,
                              translator=SystemCapacityTranslator())

class InfiniBoxSystemCapacity(SystemObject):
    URL_PATH = URL("/api/rest/system/capacity")
    FIELDS = [
        Field("id", binding=ConstBinding('capacity'), is_identity=True, cached=True),
        Field("free_physical_capacity", api_name="free_physical_space", type=SystemCapacityType),
        Field("free_virtual_capacity", api_name="free_virtual_space", type=SystemCapacityType),
        Field("total_physical_capacity", type=SystemCapacityType),
        Field("total_virtual_capacity", type=SystemCapacityType, mutable=True)
    ]

    def __init__(self, system):
        super(InfiniBoxSystemCapacity, self).__init__(system, {})

    @cached_method
    def get_this_url_path(self):
        return self.URL_PATH
