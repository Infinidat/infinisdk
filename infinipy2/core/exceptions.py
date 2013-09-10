class InfinipyException(Exception):
    pass

class APICommandException(InfinipyException):
    pass

class APICommandFailed(APICommandException):
    def __init__(self, response, *args, **kwargs):
        self.response = response
        super(APICommandFailed, self).__init__(*args, **kwargs)
