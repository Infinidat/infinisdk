from ..core import Field
from ..core.bindings import (
    RelatedObjectBinding,
    ListOfRelatedObjectIDsBinding
)
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject


class SMBUser(InfiniBoxObject):
    URL_PATH = "smb_users"
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field(
            "tenant",
            type="infinisdk.infinibox.tenant:Tenant",
            api_name="tenant_id",
            binding=RelatedObjectBinding("tenants"),
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "name",
            creation_parameter=True,
            mutable=True,
            default=Autogenerate("smb_user_{short_uuid}"),
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "password",
            creation_parameter=True,
            hidden=True,
            mutable=True,
            default="a@123456789",
        ),
        Field(
            "enabled",
            type=bool,
            mutable=True,
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "sid",
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "privileges",
            type=list,
            creation_parameter=True,
            optional=True,
            mutable=True,
        ),
        Field(
            "primary_group",
            api_name="primary_group_id",
            type="infinisdk.infinibox.smb_group:SMBGroup",
            binding=RelatedObjectBinding("smb_groups"),
            mutable=True,
        ),
        Field(
            "groups",
            api_name="group_ids",
            type=list,
            binding=ListOfRelatedObjectIDsBinding("smb_groups"),
            is_filterable=True,
            mutable=True,
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "smb_user"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb()
