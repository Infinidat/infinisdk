import arrow
from urlobject import URLObject as URL

from munch import munchify

class InfiniSDKException(Exception):
    pass

class InfiniSDKRuntimeException(InfiniSDKException):
    pass

class InvalidUsageException(InfiniSDKException):
    pass

class UnknownSystem(InfiniSDKException):
    pass

class InvalidOperationException(InfiniSDKException):
    pass

class CacheMiss(InfiniSDKException):
    pass

class APICommandException(InfiniSDKException):
    pass

class CannotGetReplicaState(InfiniSDKException):
    pass

class BadFilepathException(InfiniSDKException):
    pass

class SystemNotFoundException(APICommandException):
    def __init__(self, err, api_request, start_timestamp):
        self.start_timestamp = start_timestamp
        self.err = err
        self.api_request = api_request
        self.address = URL(api_request.url).hostname
        super(SystemNotFoundException, self).__init__("Cannot connect {}".format(self.address))

class APITransportFailure(APICommandException):
    def __init__(self, system, request_kwargs, err, api_request, start_timestamp):
        super(APITransportFailure, self).__init__('APITransportFailure: {}'.format(err))
        self.start_timestamp = start_timestamp
        self.err = err
        self.api_request = api_request
        self.system = system
        self.address = URL(api_request.url).hostname
        self.attrs = munchify(request_kwargs)
        self.error_desc = str(err)

    @property
    def request_timestamp(self):
        return arrow.Arrow.fromtimestamp(self.start_timestamp)

    def __repr__(self):
        return ("API Transport Failure on {system_name}\n\t"
                "Request: {e.attrs.method} {e.api_request.url}\n\t"
                "Request Timestamp: {e.request_timestamp}\n\t"
                "Error Description: {e.error_desc}".format(e=self, system_name=self.system.get_name()))

    __str__ = __repr__


class APICommandFailed(APICommandException):
    def __init__(self, response):
        super(APICommandFailed, self).__init__(response)
        self.response = response
        self.status_code = self.response.response.status_code
        json = response.get_json()
        error = response.get_error()
        self.error_code = error.get('code') if error else None
        if json is None:
            message = "[{}]".format(response.response.content)
        else:
            message = (json.get("error") or {}).get("message", "?")
        self.reasons = self._parse_reasons(error or {})
        self.message = message
        self.address = URL(response.response.request.url).hostname

    @classmethod
    def raise_from_response(cls, response):
        error = response.get_error() or {}
        if error.get('is_remote', False):
            cls = RemoteAPICommandFailed  # pylint: disable=self-cls-assignment
        raise cls(response)

    def _parse_reasons(self, error):
        returned = []
        for reason in (error.get('reasons') or []):
            returned.append(ErrorReason.from_dict(reason))
        return returned

    def __repr__(self):
        returned = ("API Command Failed\n\t"
                    "Request: {e.response.method} {e.response.url}\n\t"
                    "Request Timestamp: {e.request_timestamp}\n\t"
                    "Response Timestamp: {e.response_timestamp}\n\t"
                    "Data: {e.sent_data_truncated}\n\t"
                    "Status: {e.status_code}\n\t"
                    "Code: {e.error_code}\n\t"
                    "Message: {e.message}".format(e=self))

        cookies = self.response.response.request.headers.get('cookie')
        if cookies:
            returned += "\n\tCookies: {}".format(cookies)
        if self.reasons:
            returned += "\n\tReasons:"
            for reason in self.reasons:
                returned += "\n\t\t{}".format(reason)
        return returned

    @property
    def sent_data_truncated(self):
        max_length = 500
        returned = repr(self.response.sent_data)
        if len(returned) > max_length:
            returned = returned[:max_length - 3 - 1] + '...' + returned[-1:]
        return returned

    @property
    def request_timestamp(self):
        return arrow.Arrow.fromtimestamp(self.response.start_time)

    @property
    def response_timestamp(self):
        return arrow.Arrow.fromtimestamp(self.response.end_time)

    def __str__(self):
        return repr(self)


class RemoteAPICommandFailed(APICommandFailed):
    pass


class ErrorReason:

    def __init__(self, message, affected_entities):
        super(ErrorReason, self).__init__()
        self.message = message
        self.affected_entities = affected_entities

    def __repr__(self):
        return self.message

    @classmethod
    def from_dict(cls, d):
        return cls(message=d['message'], affected_entities=d['affected_entities'])

class CommandNotApproved(APICommandFailed):
    def __init__(self, response, reason):
        super(CommandNotApproved, self).__init__(response)
        self.reason = reason

    def __repr__(self):
        return "Command forbidden without explicit approval ({})".format(self.reason)

class CapacityUnavailable(APICommandException):
    pass

class ObjectNotFound(InfiniSDKException):
    """Thrown when using .get(), when no results are found but the code expects a single object
    """

class TooManyObjectsFound(InfiniSDKException):
    """Thrown when using .get(), when more than one result is found but the code expects a single object
    """

class MissingFields(InfiniSDKException):
    pass


class ChangedDuringIteration(InfiniSDKException, IndexError):
    pass


class AttributeAlreadyExists(InfiniSDKException):
    def __init__(self, obj, attr):
        self._obj = obj
        self._attr = attr
        msg = "{} already exists for {}".format(attr, obj)
        super(AttributeAlreadyExists, self).__init__(msg)

class VersionNotSupported(InfiniSDKException):
    def __init__(self, version):
        msg = "System version '{}' is not supported by this version of InfiniSDK".format(version)
        super(VersionNotSupported, self).__init__(msg)

class MethodDisabled(InfiniSDKException):
    """Thrown when attempting to use an HTTP method, which has been explicitly disabled"""
    pass
