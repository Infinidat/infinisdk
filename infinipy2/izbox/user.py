from ..core import SystemObject, Field
from ..core.system_object_utils import make_getter_updater
from ..core.api.special_values import Autogenerate

class User(SystemObject):

    FIELDS = [
        Field("id", is_identity=True),
        Field("role", mandatory=True, default="INFINIDAT"),
        Field("email", mandatory=True, default=Autogenerate("user{time}@infinidat.com")),
        Field("username", mandatory=True, default=Autogenerate("user_{ordinal}")),
        Field("password", mandatory=True, default="12345678"),
    ]
