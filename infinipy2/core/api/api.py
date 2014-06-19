import json
from contextlib import contextmanager

import requests
from logbook import Logger
from sentinels import NOTHING

from .special_values import translate_special_values
from ..._compat import httplib, get_timedelta_total_seconds, string_types
from ..exceptions import APICommandFailed, CommandNotApproved, APITransportFailure
from urlobject import URLObject as URL

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

class API(object):
    def __init__(self, target):
        super(API, self).__init__()
        self.system = target
        self._default_request_timeout = self.system.get_api_timeout()
        self._approved = True
        self._session = None
        self._session = requests.Session()
        self.set_auth(*self.system.get_api_auth())
        self._session.auth = self.system.get_api_auth()
        self._session.headers["content-type"] = "application/json"
        self._urls = [self._url_from_address(address) for address in target.get_api_addresses()]
        self._active_url = None

    @contextmanager
    def get_approval_context(self, value):
        old_approved_value = self._approved
        self._approved = value
        try:
            yield
        finally:
            self._approved = old_approved_value

    def get_approved_context(self):
        return self.get_approval_context(True)

    def get_unapproved_context(self):
        return self.get_approval_context(False)

    def set_auth(self, username_or_auth, password=NOTHING):
        """
        Sets the username and password under which operations will be performed

        Can be used both with a uple argument or with two arguments (username, password):

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
            if http_method != "get" and self._approved and not path.startswith("/api/internal/"):
                full_url = full_url.add_query_param("approved", "true")
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
        try:
            returned = self._request(http_method, path, **kwargs)
        except requests.exceptions.RequestException as e:
            raise APITransportFailure(e)

        if assert_success:
            try:
                returned.assert_success()
            except APICommandFailed as e:
                if e.response.get_error():
                    if e.response.get_error().get('code') in self.system.get_approval_failure_codes():
                        raise CommandNotApproved(e.response)
                raise
        return returned

    def _get_possible_urls(self, address=None):

        if address is not None:
            return [self._url_from_address(address)]

        if self._active_url is not None:
            return [self._active_url]

        return self._urls

    def _url_from_address(self, address):
        return URL("http://{0}:{1}".format(*address)).add_path("/api/rest")


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
        try:
            return self.response.json()
        except ValueError:
            return None

    def _get_result(self):
        return self.get_json()["result"]

    def get_result(self):
        return self._get_result()

    def get_error(self):
        json = self.get_json()
        if json is not None:
            return json["error"]

    def __repr__(self):
        return repr(self.response)

    def get_metadata(self):
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
