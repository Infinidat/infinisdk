from ..core import Field
from ..core.bindings import RelatedObjectBinding
from .system_object import InfiniBoxObject


class NFSUser(InfiniBoxObject):
    URL_PATH = "nfs_users"
    FIELDS = [
        Field(
            "id",
            type=int,
            is_identity=True,
            is_filterable=True,
            is_sortable=True,
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
            "uid",
            creation_parameter=True,
            type=int,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "primary_group_id",
            creation_parameter=True,
            type=int,
            mutable=True,
        ),
        Field(
            "supplementary_groups",
            type=list,
            mutable=True,
        ),
        Field(
            "sid",
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_smb_dual_protocol",
        ),
        Field(
            "primary_group_gsid",
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_smb_dual_protocol",
        ),
        Field(
            "supplementary_groups_gsid",
            type=list,
            mutable=True,
            feature_name="native_smb_dual_protocol",
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "nfs_user"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb_dual_protocol()
