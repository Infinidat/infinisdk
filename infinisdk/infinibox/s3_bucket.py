from infinisdk.core.api.special_values import Autogenerate
from infinisdk.core.bindings import RelatedObjectBinding
from infinisdk.core.translators_and_types import CapacityType, MillisecondsDatetimeType
from infinisdk.core.type_binder import TypeBinder

from ..core import Field
from .system_object import InfiniBoxObject


class S3BucketsBinder(TypeBinder):
    def create_many(self, *args, **kwargs):
        """
        Creates multiple S3 buckets with a single call. Parameters are just like ``s3_buckets.create``, only with the
        addition of the ``count`` parameter

        Returns: list of S3 buckets

        :param count: number of S3 buckets to create. Defaults to 1.
        """
        name = kwargs.pop("name", None)
        if name is None:
            name = self.fields.name.generate_default().generate()
        count = kwargs.pop("count", 1)
        return [
            self.create(*args, name="{}-{}".format(name, i), **kwargs)
            for i in range(1, count + 1)
        ]


class S3Bucket(InfiniBoxObject):
    BINDER_CLASS = S3BucketsBinder

    URL_PATH = "s3_buckets"

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
            default=Autogenerate("bucket-{uuid}"),
        ),
        Field(
            "account",
            type="infinisdk.infinibox.s3_account:S3Account",
            api_name="account_id",
            binding=RelatedObjectBinding("s3_accounts"),
            creation_parameter=True,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "account_name",
            type=str,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "used_size",
            api_name="capacity_consumed",
            type=CapacityType,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "capacity_savings",
            type=CapacityType,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "disk_usage",
            type=int,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "data_reduction_ratio",
            type=float,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "allocated",
            type=CapacityType,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "tree_allocated",
            type=CapacityType,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "compression_suppressed",
            type=bool,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "capacity_savings_per_entity",
            type=CapacityType,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "compression_enabled",
            type=bool,
            mutable=True,
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
            feature_name="native_s3",
            toggle_name="compression",
        ),
        Field(
            "ssd_enabled",
            type=bool,
            mutable=True,
            creation_parameter=True,
            is_filterable=True,
            is_sortable=True,
            optional=True,
            toggle_name="ssd",
            feature_name="native_s3",
        ),
        Field(
            "created_at",
            type=MillisecondsDatetimeType,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "updated_at",
            type=MillisecondsDatetimeType,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "object_count",
            type=int,
            is_sortable=True,
            is_filterable=True,
            feature_name="native_s3",
        ),
        Field(
            "pool",
            type="infinisdk.infinibox.pool:Pool",
            api_name="pool_id",
            is_filterable=True,
            is_sortable=True,
            binding=RelatedObjectBinding(),
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "s3_bucket"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_s3()
