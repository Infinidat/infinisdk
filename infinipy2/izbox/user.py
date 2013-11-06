from ..core import SystemObject, Field
from ..core.system_object_utils import make_getter_updater

class User(SystemObject):
    FIELDS = [
        Field("id", is_identity=True),
        Field("role"),
        Field("email"),
        Field("username"),
    ]
