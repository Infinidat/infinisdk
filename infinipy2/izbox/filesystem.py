from capacity import byte
from ..core import SystemObject, Field, FunctionTranslator

class Filesystem(SystemObject):
    FIELDS = [
        Field("id"),
        Field("quota", api_name="quota_in_bytes",
              translator=FunctionTranslator(to_api=lambda x: int(x // byte), from_api=lambda x: int(x) * byte)),
        Field("name"),
    ]
