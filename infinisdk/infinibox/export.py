from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.translators_and_types import MunchListType
from .system_object import InfiniBoxObject
from ..core.bindings import RelatedObjectNamedBinding, RelatedObjectBinding


class _Field(Field):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('is_sortable', True)
        kwargs.setdefault('is_filterable', True)
        super(_Field, self).__init__(*args, **kwargs)


class Export(InfiniBoxObject):
    FIELDS = [
        _Field("id", is_identity=True, type=int),
        _Field("export_path", creation_parameter=True, default=Autogenerate("/{prefix}export_{uuid}")),
        _Field("inner_path", creation_parameter=True, optional=True),
        Field("filesystem", api_name="filesystem_id", creation_parameter=True, cached=True, type=int,
              binding=RelatedObjectNamedBinding()),
        _Field("enabled", type=bool, mutable=True, creation_parameter=True, optional=True),
        _Field("make_all_users_anonymous", type=bool, mutable=True, creation_parameter=True, optional=True),
        _Field("anonymous_gid", type=int, mutable=True, creation_parameter=True, optional=True),
        _Field("anonymous_uid", type=int, mutable=True, creation_parameter=True, optional=True),
        _Field("privileged_port", type=bool, mutable=True, creation_parameter=True, optional=True),
        _Field("transport_protocols", creation_parameter=True, optional=True, mutable=True),
        _Field("32bit_file_id", type=bool, mutable=True, creation_parameter=True, optional=True),
        _Field("pref_readdir", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        _Field("pref_read", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        _Field("pref_write", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        _Field("max_read", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        _Field("max_write", creation_parameter=True, optional=True, type=CapacityType, mutable=True),
        Field("permissions", type=MunchListType, creation_parameter=True, optional=True, mutable=True),
        _Field("created_at", type=MillisecondsDatetimeType),
        _Field("updated_at", type=MillisecondsDatetimeType),
        _Field("snapdir_visible", type=bool, creation_parameter=True, optional=True, mutable=True,
               feature_name="dot_snapshot"),
        _Field("tenant", api_name="tenant_id", binding=RelatedObjectBinding('tenants'),
               type='infinisdk.infinibox.tenant:Tenant', feature_name='tenants'),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_nas()
