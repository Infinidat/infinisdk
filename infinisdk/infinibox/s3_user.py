from infinisdk.core.api.special_values import Autogenerate
from infinisdk.core.bindings import RelatedObjectBinding
from infinisdk.core.type_binder import TypeBinder

from ..core import Field, MillisecondsDatetimeType
from .system_object import InfiniBoxObject


class S3UsersBinder(TypeBinder):
    def create_many(self, *args, **kwargs):
        """
        Creates multiple S3 users with a single call. Parameters are just like ``s3_users.create``, only with the
        addition of the ``count`` parameter

        Returns: list of S3 users

        :param count: number of S3 users to create. Defaults to 1.
        """
        name = kwargs.pop("name", None)
        if name is None:
            name = self.fields.name.generate_default().generate()
        count = kwargs.pop("count", 1)
        return [
            self.create(*args, name="{}-{}".format(name, i), **kwargs)
            for i in range(1, count + 1)
        ]


class S3User(InfiniBoxObject):
    BINDER_CLASS = S3UsersBinder

    URL_PATH = "s3_users"

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
            "name",
            type=str,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
            default=Autogenerate("user_{uuid15}"),
        ),
        Field(
            "account_name",
            type=str,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "account",
            type="infinisdk.infinibox.s3_account:S3Account",
            binding=RelatedObjectBinding("s3_accounts"),
            api_name="account_id",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
        ),
        Field(
            "canonical_id",
            type=str,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "status",
            type=str,
            is_sortable=True,
            is_filterable=True,
            mutable=True,
            feature_name="native_s3",
        ),
        Field(
            "root",
            api_name="is_root",
            type=bool,
            creation_parameter=True,
            optional=True,
            is_sortable=True,
            is_filterable=True,
            mutable=True,
            feature_name="native_s3",
        ),
        Field(
            "gid",
            type=int,
            is_sortable=True,
            is_filterable=True,
            mutable=True,
            feature_name="native_s3",
        ),
        Field(
            "uid",
            type=int,
            is_sortable=True,
            is_filterable=True,
            mutable=True,
            feature_name="native_s3",
        ),
        Field(
            "description",
            type=str,
            creation_parameter=True,
            optional=True,
            is_sortable=True,
            is_filterable=True,
            mutable=True,
            feature_name="native_s3",
        ),
        Field(
            "last_used",
            type=MillisecondsDatetimeType,
            feature_name="native_s3",
        ),
        Field(
            "num_credentials",
            type=int,
            is_sortable=True,
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
        return "s3_user"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_s3()
