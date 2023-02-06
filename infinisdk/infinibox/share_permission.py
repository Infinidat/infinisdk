from ..core import Field
from ..core.bindings import RelatedObjectBinding
from .system_object import InfiniBoxSubObject


class SharePermission(InfiniBoxSubObject):
    URL_PATH = "permissions"

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field(
            "share",
            type="infinisdk.infinibox.share:Share",
            binding=RelatedObjectBinding("shares"),
            api_name="share_id",
            is_filterable=True,
            is_sortable=True,
            creation_parameter=False,
            optional=False,
            use_in_repr=True,
            is_parent_field=True,
        ),
        Field(
            "sid",
            creation_parameter=True,
            optional=False,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "access",
            mutable=True,
            optional=False,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
        ),
    ]

    @classmethod
    def get_plural_name(cls):
        return "permissions"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb()
