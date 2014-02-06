from capacity import byte, GB
from ..core import SystemObject
from ..core.field import Field
from api_object_schema import FunctionTranslator
from ..core.system_object_utils import make_getter_updater, make_getter
from ..core.api.special_values import Autogenerate

class Filesystem(SystemObject):
    FIELDS = [
        Field("id", is_identity=True),
        Field("quota", api_name="quota_in_bytes",
              default=GB, mandatory=True,
              translator=FunctionTranslator(to_api=lambda x: int(x // byte), from_api=lambda x: int(x) * byte)),
        Field("name", mandatory=True, default=Autogenerate("fs_{uuid}")),

        Field("cifs_access_list", mandatory=True, type=list, default=[{"read_only": False, "username": "Everyone"}]),
        Field("nfs_access_list",  mandatory=True, type=list, default=[{"allow_root_access": False, "host": "*", "read_only": False, "secure": True}]),

        Field("compression_type", mandatory=True, default="off"),
        Field("owned_by",         mandatory=True, default="CUSTOMER"),
        Field("permissions",      mandatory=True, type=int, default=0o777),
        Field("shared_by_cifs",   mandatory=True, type=bool, default=True),
        Field("shared_by_nfs",    mandatory=True, type=bool, default=True),
        Field("user_id",          mandatory=True, type=int, default=0),
        Field("group_id",         mandatory=True, type=int, default=0),
    ]

    get_quota, update_quota = make_getter_updater("quota")

    get_name, update_name = make_getter_updater("name")

    get_mount_path = make_getter("mount_path")

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

