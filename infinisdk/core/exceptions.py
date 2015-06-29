###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from munch import munchify

class InfiniSDKException(Exception):
    pass

class InfiniSDKRuntimeException(InfiniSDKException):
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

class SystemNotFoundException(APICommandException):
    def __init__(self, msg, sys_address=None):
        super(SystemNotFoundException, self).__init__(msg)
        self.address = sys_address

class APITransportFailure(APICommandException):
    def __init__(self, request_kwargs, err):
        super(APITransportFailure, self).__init__('APITransportFailure: {0}'.format(err))
        self.err = err
        self.attrs = munchify(request_kwargs)
        self.error_desc = str(err)

    def __repr__(self):
        return ("API Transport Failure\n\t"
                "Request: {self.attrs.method} {self.attrs.url}\n\t"
                "Error Description: {self.error_desc}".format(self=self))

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
    def __init__(self, response, reason):
        super(CommandNotApproved, self).__init__(response)
        self.reason = reason

    def __repr__(self):
        return "Command forbidden without explicit approval ({0})".format(self.reason)

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

class AttributeAlreadyExists(InfiniSDKException):
    def __init__(self, obj, attr):
        self._obj = obj
        self._attr = attr
        msg = "{0} already exists for {1}".format(attr, obj)
        super(AttributeAlreadyExists, self).__init__(msg)

class VersionNotSupported(InfiniSDKException):
    def __init__(self, version):
        msg = "System version '{0}' is not supported by this version of InfiniSDK".format(version)
        super(VersionNotSupported, self).__init__(msg)
