class InfinipyException(Exception):
    pass

class APICommandException(InfinipyException):
    pass

class APICommandFailed(APICommandException):
    def __init__(self, response, *args, **kwargs):
        self.response = response
        super(APICommandFailed, self).__init__(*args, **kwargs)

class CommandNotApproved(APICommandException):
    def __init__(self, response):
        reasons = []
        json = response.json()
        if json is not None:
            reasons.extend((json.get("error") or {}).get("reasons", ()))
        super(CommandNotApproved, self).__init__("Command forbidden without explicit approval ({})".format(", ".join(reasons), reasons))

    def __repr__(self):
        return self.msg


class ObjectNotFound(InfinipyException):
    pass

class TooManyObjectsFound(InfinipyException):
    pass

class MissingFields(InfinipyException):
    pass
