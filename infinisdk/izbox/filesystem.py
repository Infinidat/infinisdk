from capacity import GB
from ..core import SystemObject, CapacityType
from ..core.field import Field
from ..core.api.special_values import Autogenerate

class Filesystem(SystemObject):
    FIELDS = [
        Field("id", is_identity=True),
        Field("quota", api_name="quota_in_bytes",
              type=CapacityType,
              default=GB, creation_parameter=True, mutable=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("fs_{uuid}")),
        Field("mount_path", type=str),

        Field("cifs_access_list", creation_parameter=True, mutable=True, type=list, default=[{"read_only": False, "username": "Everyone"}]),
        Field("nfs_access_list",  creation_parameter=True, mutable=True, type=list, default=[{"allow_root_access": False, "host": "*", "read_only": False, "secure": True}]),

        Field("compression_type", creation_parameter=True, mutable=True, default="off"),
        Field("owned_by",         creation_parameter=True, mutable=True, default="CUSTOMER"),
        Field("permissions",      creation_parameter=True, mutable=True, type=int, default=0o777),
        Field("shared_by_cifs",   creation_parameter=True, mutable=True, type=bool, default=True),
        Field("shared_by_nfs",    creation_parameter=True, mutable=True, type=bool, default=True),
        Field("user_id",          creation_parameter=True, mutable=True, type=int, default=0),
        Field("group_id",         creation_parameter=True, mutable=True, type=int, default=0),
    ]

    def create_snapshot(self, name=Autogenerate("snapshot_{uuid}")):
        resp = self.system.api.post("snapshots", data={"filesystem_id": self.id, "snapshot_name": name})
        return Snapshot(self.system, resp.get_result())

    def rollback(self, snapshot):
        self.system.api.post("filesystems/{0}/rollback".format(self.id), data={"snapshot_id": snapshot.id})

    def get_snapshots(self):
        return self.system.snapshots.find(parent_id=self.id)

class Snapshot(Filesystem):
    @classmethod
    def create(self, system, filesystem_id, **kwargs):
        return system.filesystems.get_by_id_lazy(filesystem_id).create_snapshot(**kwargs)

    def get_parent(self):
        return self.system.filesystems.get_by_id(self.get_field("parent_id", from_cache=True))

    @classmethod
    def get_creation_defaults(cls):
        return {"name": Filesystem.fields.name.generate_default().generate()}
