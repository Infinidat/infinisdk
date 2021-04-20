from ..core import Field
from ..core.bindings import RelatedObjectBinding
from .system_object import InfiniBoxObject


class ActiveDirectoryDomains(InfiniBoxObject):
    URL_PATH = "activedirectory/domains"
    UID_FIELD = "domain"
    FIELDS = [
        Field(
            "domain",
            creation_parameter=True,
        ),
        Field(
            "org_unit",
            creation_parameter=True,
            optional=True,
        ),
        Field(
            "preferred_ips",
            type=list,
            creation_parameter=True,
        ),
        Field(
            "username",
            creation_parameter=True,
        ),
        Field(
            "password",
            creation_parameter=True,
            hidden=True,
        ),
        Field(
            "tenant",
            type="infinisdk.infinibox.tenant:Tenant",
            api_name="tenant_id",
            binding=RelatedObjectBinding("tenants"),
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "active_directory_domain"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb()
