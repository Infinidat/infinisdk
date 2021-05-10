from ..core import Field
from ..core.bindings import RelatedObjectBinding

from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject


class SMBGroup(InfiniBoxObject):
    URL_PATH = "smb_groups"
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
            default=Autogenerate("smb_group_{uuid}"),
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
            "domain_members",
            type=list,
            creation_parameter=True,
            optional=True,
            mutable=True,
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "smb_group"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb()
