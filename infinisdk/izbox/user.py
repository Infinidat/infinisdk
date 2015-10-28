from ..core import SystemObject, Field
from ..core.api.special_values import Autogenerate

class User(SystemObject):

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("role", creation_parameter=True, mutable=True, default="INFINIDAT"),
        Field("email", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}@infinidat.com")),
        Field("name", api_name="username", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}")),
        Field("password", creation_parameter=True, mutable=True, default="12345678"),
    ]
