from ..core.q import Q
from ..core import Field
from ..core.api.special_values import Autogenerate, OMIT
from ..core.bindings import RelatedObjectBinding
from .dataset import Dataset, DatasetTypeBinder
from .treeq import TreeQBinder



class FilesystemBinder(DatasetTypeBinder):
    def __init__(self, object_type, system):
        super(FilesystemBinder, self).__init__(object_type, system)
        self._treeq_binders = {}

    def get_or_create_treeq_binder(self, filesystem):
        filesystem_id = filesystem.get_id()
        if filesystem_id not in self._treeq_binders:
            self._treeq_binders[filesystem_id] = TreeQBinder(self.system, filesystem)
        return self._treeq_binders[filesystem_id]

    def delete_treeq_binder(self, filesystem):
        self._treeq_binders.pop(filesystem.get_id(), None)

    def get_treeq_binder_by_id(self, filesystem_id):
        return self._treeq_binders[filesystem_id]


class Filesystem(Dataset):
    FIELDS = [
        Field("parent", type='infinisdk.infinibox.filesystem:Filesystem', cached=True, api_name="parent_id",
              binding=RelatedObjectBinding('filesystems'), is_filterable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True,
              is_sortable=True, default=Autogenerate("fs_{uuid}")),
        Field("root_mode", creation_parameter=True, hidden=True, optional=True),
        Field("atime_mode", is_filterable=True, is_sortable=True),
        Field("established", api_name="_is_established", type=bool, is_filterable=True, is_sortable=True, new_to="4.0"),
        Field('data_snapshot_guid', is_filterable=True, is_sortable=True, feature_name="nas_replication"),
        Field("snapdir_name", creation_parameter=True, optional=True, is_filterable=True, is_sortable=True,
              feature_name="dot_snapshot"),
        Field("visible_in_snapdir", type=bool, is_filterable=True, is_sortable=True, feature_name="dot_snapshot"),
        Field("snapdir_accessible", type=bool, feature_name="dot_snapshot", creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True)
    ]

    BINDER_CLASS = FilesystemBinder

    def __init__(self, system, initial_data):
        super(Filesystem, self).__init__(system, initial_data)
        self.treeqs = self.system.filesystems.get_or_create_treeq_binder(self)

    def delete(self, force_if_snapshot_locked=OMIT):
        super(Filesystem, self).delete(force_if_snapshot_locked=force_if_snapshot_locked)
        self.system.filesystems.delete_treeq_binder(self)

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_nas()

    def add_export(self, **kwargs):
        return self.system.exports.create(filesystem=self, **kwargs)

    def get_exports(self):
        return self.system.exports.find(Q.filesystem_id == self.id)
