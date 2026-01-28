from infinisdk.core.api.special_values import Autogenerate
from infinisdk.core.bindings import RelatedObjectBinding
from infinisdk.core.translators_and_types import CapacityType

from ..core import Field, MillisecondsDatetimeType
from .system_object import InfiniBoxObject


class S3Account(InfiniBoxObject):
    URL_PATH = "s3_accounts"
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
            mutable=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
            default=Autogenerate("account_{uuid}"),
        ),
        Field(
            "pool_name",
            type=str,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "pool",
            type="infinisdk.infinibox.pool:Pool",
            api_name="pool_id",
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            binding=RelatedObjectBinding(),
        ),
        Field(
            "canonical_id",
            type=str,
            creation_parameter=True,
            optional=True,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "email",
            type=str,
            creation_parameter=True,
            optional=True,
            mutable=True,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "location",
            type=str,
            creation_parameter=True,
            optional=True,
            mutable=True,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "enabled",
            type=bool,
            creation_parameter=True,
            optional=True,
            mutable=True,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "capacity_consumed",
            type=CapacityType,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "buckets_count",
            type=int,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "users_count",
            type=int,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "credentials_count",
            type=int,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
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
    ]

    @classmethod
    def get_type_name(cls):
        return "s3_account"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_s3()
