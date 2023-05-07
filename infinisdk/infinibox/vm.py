from ..core import Field
from ..core.system_object import SystemObject


class Vm(SystemObject):

    FIELDS = [
        Field(
            "id",
            type=int,
            cached=True,
            is_identity=True,
            is_sortable=True,
            is_filterable=True,
        ),
        Field("uuid", type=str, cached=True, is_filterable=True, is_sortable=True),
        Field(
            "name",
            type=str,
            cached=True,
            is_filterable=True,
            is_sortable=True,
            mutable=True,
            add_getter=True,
        ),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_vvol()
