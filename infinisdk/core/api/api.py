###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
import json
import sys
from contextlib import contextmanager

import requests
from logbook import Logger
from sentinels import NOTHING, Sentinel
from urlobject import URLObject as URL

import colorama

from ..._compat import get_timedelta_total_seconds, httplib, string_types
from ..config import config
from ..exceptions import (APICommandFailed, APITransportFailure,
                          CommandNotApproved)
from .special_values import translate_special_values

_logger = Logger(__name__)

def _get_request_delegate(http_method):
    def returned(self, *args, **kwargs):
        return self.request(http_method, *args, **kwargs)
    returned.__name__ = http_method
    returned.__doc__ = "Shortcut for :func:`.request({0!r}) <API.request>`".format(http_method)
    return returned

def _join_path(url, path):
    _url = URL(url)
    path = URL(path)
    if path.path:
        _url = _url.add_path(path.path)
    if path.query:
        _url = _url.with_query(path.query)
    return _url

_INTERACTIVE = Sentinel('INTERACTIVE')

class API(object):
    def __init__(self, target, use_ssl, ssl_cert):
        super(API, self).__init__()
        self.system = target
        self._use_ssl = use_ssl
        self._ssl_cert = ssl_cert
        self._default_request_timeout = self.system.get_api_timeout()
        self._approved = True
        self._session = requests.Session()
        assert self._session.cert is None
        self._session.cert = ssl_cert
        if not ssl_cert:
            self._session.verify = False
        self.set_auth(*self.system.
                      get_api_auth())
        self._session.auth = self.system.get_api_auth()
        self._session.headers["content-type"] = "application/json"
        self._urls = [self._url_from_address(address, use_ssl) for address in target.get_api_addresses()]
        self._active_url = None
        self._checked_version = False

    @contextmanager
    def get_approval_context(self, value):
        """A context manager that controls whether requests are automatically approved (confirmed)
        """
        old_approved_value = self._approved
        self._approved = value
        try:
            yield
        finally:
            self._approved = old_approved_value

    def get_approved_context(self):
        """A context marking all operations as approved (confirmed)"""
        return self.get_approval_context(True)

    def get_unapproved_context(self):
        """A context marking all operations as unapproved (not confirmed)"""
        return self.get_approval_context(False)

    def set_interactive_approval(self):
        """Causes an interactive prompt whenever a command requires approval from the user"""
        self._approved = _INTERACTIVE

    def set_auth(self, username_or_auth, password=NOTHING):
        """
        Sets the username and password under which operations will be performed

        Can be used both with a tuple argument or with two arguments (username, password):

        >>> system.set_auth(('username', 'password'))
        >>> system.set_auth('username', 'password')
        """
        if isinstance(username_or_auth, tuple):
            if password is not NOTHING:
                raise TypeError("Auth given as tuple, but password was used")
            username, password = username_or_auth
        else:
            if password is NOTHING:
                raise TypeError("Password not specified")
            username = username_or_auth

        self._session.auth = (username, password)

    def get_auth(self):
        """
        Returns a tuple of the current username/password used by the API
        """
        return self._session.auth

    @contextmanager
    def auth_context(self, username, password):
        """
        Changes the API auth information for the duration of the context:

        >>> with system.api.auth_context('username', 'password'):
        ...     ... # execute operations as 'username'
        """
        auth = (username, password)
        prev = self.get_auth()
        self.set_auth(*auth)
        try:
            yield
        finally:
            self.set_auth(*prev)

    get = _get_request_delegate("get")
    put = _get_request_delegate("put")
    post = _get_request_delegate("post")
    patch = _get_request_delegate("patch")
    delete = _get_request_delegate("delete")

    def _request(self, http_method, path, assert_success=True, **kwargs):
        """
        Sends a request to the system API interface

        :rtype: :class:`.Response`
        """
        if not self._checked_version and config.root.check_version_compatibility:
            self._checked_version = True
            try:
                self.system.check_version()
            except:
                self._checked_version = False
                raise

        returned = None
        kwargs.setdefault("timeout", self._default_request_timeout)
        raw_data = kwargs.pop("raw_data", False)
        data = kwargs.pop("data", None)
        if data is not None and not isinstance(data, string_types):
            if not raw_data:
                data = translate_special_values(data)
            data = json.dumps(data)

        specified_address = kwargs.pop("address", None)
        urls = self._get_possible_urls(specified_address)

        for url in urls:
            full_url = _join_path(url, URL(path))
            # TODO: make approved deduction smarter
            if http_method != "get" and self._approved == True and not path.startswith("/api/internal/"):
                full_url = self._with_approved(full_url)
            hostname = full_url.hostname
            _logger.debug("{0} <-- {1} {2}", hostname, http_method.upper(), full_url)
            if data is not None:
                _logger.debug("{0} <-- DATA: {1}" , hostname, data)
            response = self._session.request(http_method, full_url, data=data, **kwargs)
            elapsed = get_timedelta_total_seconds(response.elapsed)
            _logger.debug("{0} --> {1} {2} (took {3:.04f}s)", hostname, response.status_code, response.reason, elapsed)
            returned = Response(http_method, full_url, data, response)
            _logger.debug("{0} --> {1}", hostname, returned.get_json())
            if response.status_code != httplib.SERVICE_UNAVAILABLE:
                if specified_address is None: # need to remember our next API target
                    self._active_url = url
                break
        return returned

    def request(self, http_method, path, assert_success=True, **kwargs):
        did_interactive_confirmation = False
        while True:
            try:
                returned = self._request(http_method, path, **kwargs)
            except requests.exceptions.RequestException as e:
                raise APITransportFailure(e)

            if assert_success:
                try:
                    returned.assert_success()
                except APICommandFailed as e:
                    if self._is_approval_required(e):
                        reason = self._get_unapproved_reason(e.response.response.json())
                        exception = CommandNotApproved(e.response, reason)
                        if self._approved is _INTERACTIVE and not did_interactive_confirmation:
                            did_interactive_confirmation = True
                            if self._ask_approval_interactively(http_method, path, reason):
                                path = self._with_approved(path)
                                continue
                            raise exception
                    raise
            return returned

    def _with_approved(self, path):
        return path.set_query_param('approved', 'true')

    def _ask_approval_interactively(self, method, path, reason):
        if not reason:
            reason = "API operation requires approval: {0} {1}".format(method, path)
        msg = "{0} Approve? [y/N] ".format(reason)
        if sys.stdout.isatty():
            msg = colorama.Fore.YELLOW + msg + colorama.Fore.RESET
        return raw_input(msg).strip().lower() in ['yes', 'y']

    def _is_approval_required(self, exception):
        if exception.response.get_error():
            return exception.response.get_error().get('code') in self.system.get_approval_failure_codes()
        return False

    def _get_unapproved_reason(self, json):
        if json:
            error = json.get('error')
            if error:
                reasons = error.get('reasons')
                if reasons:
                    return reasons[0]
                return error.get('message')
        return None


    def _get_possible_urls(self, address=None):

        if address is not None:
            return [self._url_from_address(address, self._use_ssl)]

        if self._active_url is not None:
            return [self._active_url]

        return self._urls

    def _url_from_address(self, address, use_ssl):
        hostname, port = address
        return URL("{0}://{1}:{2}".format("https" if use_ssl else "http", hostname, port)).add_path("/api/rest")


class Response(object):
    """
    System API request response
    """
    def __init__(self, method, url, data, resp):
        super(Response, self).__init__()
        self.method = method
        #: response object as returned from ``requests``
        self.response = resp
        #: URLObject of the final location the response was obtained from
        self.url = url
        #: Data sent to on
        self.sent_data = data

    def get_json(self):
        """
        :returns: the json object returned from the system, or None if no json could be decoded
        """
        try:
            return self.response.json()
        except ValueError:
            return None

    def _get_result(self):
        return self.get_json()["result"]

    def get_result(self):
        """
        :returns: the result of the API call, extracted from the response JSON object
        """
        return self._get_result()

    def get_error(self):
        """
        :returns: the error portion of the response as returned from the system, or None if it doesn't exist
        """
        json = self.get_json()
        if json is not None:
            return json["error"]

    def __repr__(self):
        return repr(self.response)

    def get_metadata(self):
        """
        :returns: the metadata portion of the response (paging information, etc.) as returned from the system, or None
           if it doesn't exist
        """
        return self.get_json()["metadata"]

    def get_page_start_index(self):
        metadata = self.get_metadata()
        return (metadata["page"] - 1) * metadata["page_size"]

    def get_total_num_objects(self):
        return self.get_metadata()["number_of_objects"]

    def assert_success(self):
        try:
            self.response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise APICommandFailed(self)


# TODO : implement async request
