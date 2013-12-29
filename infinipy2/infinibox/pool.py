from capacity import TB
from ..core import Field, CapacityType
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject


class Pool(InfiniBoxObject):
    FIELDS = [
        Field("id", is_identity=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("pool_{uuid}")),
        Field("virtual_capacity",  creation_parameter=True, mutable=True, default=TB, type=CapacityType),
        Field("physical_capacity", creation_parameter=True, mutable=True, default=TB, type=CapacityType),
    ]

    def get_volumes(self):
        return self.system.volumes.find(pool_id=self.id)
