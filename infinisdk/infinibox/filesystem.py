from capacity import GB
from ..core.q import Q
from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from .dataset import Dataset


class Filesystem(Dataset):

    FIELDS = [
        Field("id", type=int, is_identity=True,
              is_filterable=True, is_sortable=True),
        Field(
            "name", creation_parameter=True, mutable=True, is_filterable=True,
            is_sortable=True, default=Autogenerate("fs_{uuid}")),
        Field("size", creation_parameter=True, mutable=True,
              is_filterable=True, is_sortable=True, default=GB, type=CapacityType),
        Field("used_size", api_name="used", type=CapacityType),
        Field("allocated", type=CapacityType, is_sortable=True, is_filterable=True),
        Field("tree_allocated", type=CapacityType),
        Field("pool", type='infinisdk.infinibox.pool:Pool', api_name="pool_id", creation_parameter=True, is_filterable=True, is_sortable=True,
              binding=RelatedObjectBinding()),
        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("parent", type='infinisdk.infinibox.filesystem:Filesystem', cached=True, api_name="parent_id", binding=RelatedObjectBinding('filesystems'), is_filterable=True),
        Field("provisioning", api_name="provtype", mutable=True, creation_parameter=True,
            is_filterable=True, is_sortable=True, default="THICK"),
        Field("created_at", cached=True, type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("ssd_enabled", type=bool, mutable=True, toggle_name='ssd', creation_parameter=True, is_filterable=True, is_sortable=True, optional=True),
        Field("write_protected", type=bool, mutable=True, creation_parameter=True, optional=True, is_filterable=True, is_sortable=True, toggle_name='write_protection'),
        Field("compression_enabled", type=bool, mutable=True, creation_parameter=True, optional=True, toggle_name='compression', feature_name='compression'),
        Field("compression_supressed", type=bool, feature_name='compression'),
        Field("capacity_savings", type=CapacityType, feature_name='compression'),
        Field("depth", cached=True, type=int, is_sortable=True, is_filterable=True),
        Field("mapped", type=bool, is_sortable=True, is_filterable=True),
        Field("has_children", type=bool, add_getter=False),
        Field("root_mode", creation_parameter=True, optional=True, is_filterable=True, is_sortable=True),
        Field("atime_mode", is_filterable=True, is_sortable=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_nas()

    def add_export(self, **kwargs):
        return self.system.exports.create(filesystem=self, **kwargs)

    def get_exports(self):
        return self.system.exports.find(Q.filesystem_id == self.id)
