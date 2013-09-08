class TypeInfo(object):
    def __init__(self, type, min_length=None, max_length=None, charset=None, max=None, min=None):
        super(TypeInfo, self).__init__()
        self.type = type
