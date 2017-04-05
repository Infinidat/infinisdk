from ..core.q import Q
from ..core import Field
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from .dataset import Dataset, DatasetTypeBinder


class FilesystemBinder(DatasetTypeBinder):
    pass


class Filesystem(Dataset):
    FIELDS = [
        Field("parent", type='infinisdk.infinibox.filesystem:Filesystem', cached=True, api_name="parent_id",
              binding=RelatedObjectBinding('filesystems'), is_filterable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True,
              is_sortable=True, default=Autogenerate("fs_{uuid}")),
        Field("root_mode", creation_parameter=True, hidden=True, optional=True),
        Field("atime_mode", is_filterable=True, is_sortable=True),
        Field('data_snapshot_guid', is_filterable=True, is_sortable=True, feature_name="nas_replication"),
    ]

    BINDER_CLASS = FilesystemBinder

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_nas()

    def add_export(self, **kwargs):
        return self.system.exports.create(filesystem=self, **kwargs)

    def get_exports(self):
        return self.system.exports.find(Q.filesystem_id == self.id)
