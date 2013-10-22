from capacity import byte
from ..core import SystemObject, Field, FunctionTranslator
from ..core.system_object_utils import make_getter_updater

class Filesystem(SystemObject):
    FIELDS = [
        Field("id", is_identity=True),
        Field("quota", api_name="quota_in_bytes",
              translator=FunctionTranslator(to_api=lambda x: int(x // byte), from_api=lambda x: int(x) * byte)),
        Field("name", mandatory=True),

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

class Snapshot(Filesystem):
    pass
