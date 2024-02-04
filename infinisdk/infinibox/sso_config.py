from urlobject import URLObject as URL

from ..core import Field, SystemObject
from ..core.translators_and_types import MillisecondsDatetimeType


class SSOIdentityProvider(SystemObject):
    URL_PATH = URL("config/sso/idps")

    FIELDS = [
        Field(
            "id",
            type=int,
            is_identity=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "name",
            creation_parameter=True,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "issuer",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "sign_on_url",
            creation_parameter=True,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "enabled",
            type=bool,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "signed_response",
            type=bool,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "signed_assertion",
            type=bool,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "signing_certificate",
            mutable=True,
        ),
        Field(
            "signing_certificate_serial",
        ),
        Field(
            "signing_certificate_expiry",
            type=MillisecondsDatetimeType,
        ),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_sso()

    @classmethod
    def get_plural_name(cls):
        return "sso_identity_providers"
