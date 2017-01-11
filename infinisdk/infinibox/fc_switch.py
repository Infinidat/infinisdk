from ..core import Field
from ..core.system_object import SystemObject
from ..core.translators_and_types import WWNType


class FcSwitch(SystemObject):
    URL_PATH = 'fc/switches'

    FIELDS = [
        Field("id", type=int, is_identity=True, cached=True),
        Field("wwnn", cached=True, type=WWNType),
        Field("vendor", cached=True),
        Field("name", cached=True, mutable=True),
        Field("resiliency_state"),
        Field("resiliency_bitmap"),
    ]

    @classmethod
    def get_type_name(cls):
        return "fc_switch"

    @classmethod
    def get_plural_name(cls):
        return "fc_switches"
