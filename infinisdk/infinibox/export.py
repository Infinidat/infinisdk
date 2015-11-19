from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.translators_and_types import MunchListType
from .system_object import InfiniBoxObject
from ..core.bindings import RelatedObjectBinding


class Export(InfiniBoxObject):
    FIELDS = [
        Field("id", is_identity=True, type=int),
        Field("export_path", creation_parameter=True, default=Autogenerate("/{prefix}export_{uuid}")),
        Field("inner_path", creation_parameter=True, optional=True),
        Field("filesystem", api_name = "filesystem_id", creation_parameter = True, cached=True, type=int, binding=RelatedObjectBinding()),
        Field("enabled", type=bool, mutable=True, creation_parameter=True, optional=True),
        Field("make_all_users_anonymous", type=bool, mutable=True, creation_parameter=True, optional=True),
        Field("anonymous_gid", type=int, mutable=True, creation_parameter=True, optional=True),
        Field("anonymous_uid", type=int, mutable=True, creation_parameter=True, optional=True),
        Field("privileged_port", type=bool, mutable=True, creation_parameter=True, optional=True),
        Field("transport_protocols", creation_parameter=True, optional=True, mutable=True),
        Field("32bit_file_id", type=bool, mutable=True, creation_parameter=True, optional=True),
        Field("pref_readdir", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        Field("pref_read", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        Field("pref_write", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        Field("max_read", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        Field("max_write", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        Field("permissions", type=MunchListType, creation_parameter=True, optional=True, mutable=True),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_nas()
