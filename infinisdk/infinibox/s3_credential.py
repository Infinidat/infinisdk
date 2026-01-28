from infinisdk.core.bindings import RelatedObjectBinding
from infinisdk.core.type_binder import TypeBinder

from ..core import Field, MillisecondsDatetimeType
from .system_object import InfiniBoxObject


class S3CredentialsBinder(TypeBinder):
    def create_many(self, *args, **kwargs):
        """
        Creates multiple S3 credentials with a single call. Parameters are just like ``s3_credentials.create``, only with the
        addition of the ``count`` parameter

        Returns: list of S3 credentials

        :param count: number of S3 credentials to create. Defaults to 1.
        """
        count = kwargs.pop("count", 1)
        return [self.create(*args, **kwargs) for i in range(1, count + 1)]


class S3Credential(InfiniBoxObject):
    BINDER_CLASS = S3CredentialsBinder

    URL_PATH = "s3_credentials"

    FIELDS = [
        Field(
            "id",
            type=int,
            is_identity=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "tenant",
            type="infinisdk.infinibox.tenant:Tenant",
            api_name="tenant_id",
            binding=RelatedObjectBinding("tenants"),
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "user",
            type="infinisdk.infinibox.s3_user:S3User",
            binding=RelatedObjectBinding("s3_users"),
            api_name="user_id",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "user_name",
            type=str,
            is_sortable=True,
            is_filterable=True,
        ),
        Field(
            "account_name",
            type=str,
            is_sortable=True,
            is_filterable=True,
        ),
        Field(
            "access_key",
            type=str,
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "secret_key",
            type=str,
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "status",
            type=str,
            creation_parameter=True,
            optional=True,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "description",
            type=str,
            creation_parameter=True,
            optional=True,
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "last_used",
            type=MillisecondsDatetimeType,
            feature_name="native_s3",
        ),
        Field(
            "created_at",
            type=MillisecondsDatetimeType,
            is_sortable=True,
            is_filterable=True,
        ),
        Field(
            "updated_at",
            type=MillisecondsDatetimeType,
            is_sortable=True,
            is_filterable=True,
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "s3_credential"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_s3()
