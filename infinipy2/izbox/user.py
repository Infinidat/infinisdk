from ..core import SystemObject, Field
from ..core.system_object_utils import make_getter_updater
from ..core.api.special_values import Autogenerate
from ..core.system_object_utils import make_getter_updater

class User(SystemObject):

    FIELDS = [
        Field("id", is_identity=True),
        Field("role", creation_parameter=True, mutable=True, default="INFINIDAT"),
        Field("email", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}@infinidat.com")),
        Field("name", api_name="username", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}")),
        Field("password", creation_parameter=True, mutable=True, default="12345678"),
    ]

    get_name, update_name = make_getter_updater("name")
