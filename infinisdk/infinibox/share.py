import mitba

from ..core import Field, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding, RelatedObjectNamedBinding
from ..core.type_binder import SubObjectTypeBinder
from .share_permission import SharePermission
from .system_object import InfiniBoxObject


class Share(InfiniBoxObject):
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field(
            "name",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            default=Autogenerate("share_{uuid}"),
        ),
        Field(
            "inner_path",
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "enabled",
            type=bool,
            mutable=True,
            optional=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "offline_caching",
            mutable=True,
            optional=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "access_based_enumeration",
            type=bool,
            mutable=True,
            optional=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "require_encryption",
            type=bool,
            mutable=True,
            optional=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="require_encryption",
        ),
        Field(
            "snapdir_visible",
            type=bool,
            mutable=True,
            optional=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "description",
            mutable=True,
            optional=True,
            creation_parameter=True,
        ),
        Field(
            "created_at",
            type=MillisecondsDatetimeType,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "updated_at",
            type=MillisecondsDatetimeType,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "filesystem",
            type="infinisdk.infinibox.filesystem:Filesystem",
            api_name="filesystem_id",
            binding=RelatedObjectNamedBinding(),
            is_filterable=True,
            is_sortable=True,
            creation_parameter=True,
        ),
        Field(
            "tenant",
            type="infinisdk.infinibox.tenant:Tenant",
            api_name="tenant_id",
            binding=RelatedObjectBinding("tenants"),
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "default_file_unix_permissions",
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_smb_dual_protocol",
        ),
        Field(
            "default_folder_unix_permissions",
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_smb_dual_protocol",
        ),
        Field(
            "leases_enabled",
            type=bool,
            mutable=True,
            optional=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="smb_leases",
        ),
        Field(
            "encryption",
            type=bool,
            mutable=True,
            optional=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="per_share_security",
        ),
        Field(
            "home_share",
            api_name="is_home_share",
            type=bool,
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            feature_name="smb_home_shares",
        ),
        Field(
            "internal_base_path",
            type=str,
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="smb_home_shares",
        ),
        Field(
            "user_dir_auto_create",
            type=bool,
            creation_parameter=True,
            optional=True,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="smb_home_shares",
        ),
        Field(
            "user_directory",
            type=str,
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="smb_home_shares",
        ),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb()

    @mitba.cached_property
    def permissions(self):
        return SubObjectTypeBinder(self.system, SharePermission, self)
