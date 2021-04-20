from ..core import Field
from ..core.bindings import (
    RelatedObjectBinding,
    ListOfRelatedObjectBinding,
    RelatedObjectViewBinding,
)
from ..core.api.special_values import Autogenerate
from ..core.type_binder import SMBUserBinder
from .system_object import InfiniBoxObject


class SMBUser(InfiniBoxObject):
    BINDER_CLASS = SMBUserBinder
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
            default=True,
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
            "primary_group_id",
            type=int,
            creation_parameter=True,
            mutable=True,
            optional=True,
        ),
        Field(
            "primary_group",
            type="infinisdk.infinibox.smb_group:SMBGroup",
            binding=RelatedObjectViewBinding("smb_groups"),
        ),
        Field(
            "group_ids",
            type=list,
            creation_parameter=True,
            optional=True,
            mutable=True,
        ),
        Field(
            "groups",
            type=list,
            binding=ListOfRelatedObjectBinding("smb_groups"),
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "smb_user"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb()

    def update_primary_group(self, primary_group, **kwargs):
        self.update_primary_group_id(primary_group.id, **kwargs)

    def update_groups(self, groups, **kwargs):
        self.update_group_ids([group.id for group in groups], **kwargs)
