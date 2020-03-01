from ..core.system_object import BaseSystemObject
from ..core import Field


class Vm(BaseSystemObject):

    FIELDS = [
        Field("id", type=int, cached=True, is_identity=True, is_sortable=True, is_filterable=True),
        Field("uuid", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field("name", type=str, cached=True, is_filterable=True, is_sortable=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_vvol()
