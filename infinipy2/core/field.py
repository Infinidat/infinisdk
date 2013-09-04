from .type_info import TypeInfo

class Field(object):
    def __init__(self, name, type=str):
        super(Field, self).__init__()
        self.name = name
        if not isinstance(type, TypeInfo):
            type = TypeInfo(type)
        self.type = type
