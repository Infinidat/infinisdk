class InfinipyException(Exception):
    pass

class CacheMiss(InfinipyException):
    pass

class APICommandException(InfinipyException):
    pass

class APICommandFailed(APICommandException):
    def __init__(self, response, *args, **kwargs):
        self.response = response
        super(APICommandFailed, self).__init__(*args, **kwargs)
        self.status_code = self.response.response.status_code
        json = response.get_json()
        if json is None:
            message = "[{0}]".format(response.response.content)
        else:
            message = (json.get("error") or {}).get("message", "?")
        self.message = message

    def __repr__(self):
        return ("API Command Failed\n  "
                "Request: {self.response.method} {self.response.url}\n  "
                "Status: {self.status_code}\n  "
                "Message: {self.message}".format(self=self))

    __str__ = __repr__

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
