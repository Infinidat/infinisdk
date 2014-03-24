class InfinipyException(Exception):
    pass

class InvalidOperationException(InfinipyException):
    pass

class CacheMiss(InfinipyException):
    pass

class APICommandException(InfinipyException):
    pass

class APITransportFailure(APICommandException):
    pass

class APICommandFailed(APICommandException):
    def __init__(self, response):
        super(APICommandFailed, self).__init__(response)
        self.response = response
        self.status_code = self.response.response.status_code
        json = response.get_json()
        if json is None:
            message = "[{0}]".format(response.response.content)
        else:
            message = (json.get("error") or {}).get("message", "?")
        self.message = message

    def __repr__(self):
        return ("API Command Failed\n\t"
                "Request: {self.response.method} {self.response.url}\n\t"
                "Data: {self.response.sent_data}\n\t"
                "Status: {self.status_code}\n\t"
                "Message: {self.message}".format(self=self))

    def __str__(self):
        return repr(self)

class CommandNotApproved(APICommandFailed):
    def __init__(self, response):
        super(CommandNotApproved, self).__init__(response)
        self.reasons = []
        json = response.response.json()
        if json is not None:
            self.reasons.extend((json.get("error") or {}).get("reasons") or tuple())

    def __repr__(self):
        return "Command forbidden without explicit approval ({0})".format(", ".join(self.reasons))

class CapacityUnavailable(APICommandException):
    pass

class ObjectNotFound(InfinipyException):
    pass

class TooManyObjectsFound(InfinipyException):
    pass

class MissingFields(InfinipyException):
    pass

class AttributeAlreadyExists(InfinipyException):
    def __init__(self, obj, attr):
        self._obj = obj
        self._attr = attr
        msg = "{0} already exists for {1}".format(attr, obj)
        super(AttributeAlreadyExists, self).__init__(msg)
