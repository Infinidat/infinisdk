import json
from contextlib import contextmanager

import requests
from logbook import Logger

from ..._compat import httplib
from ..exceptions import APICommandFailed
from urlobject import URLObject as URL

_logger = Logger(__name__)

def _get_request_delegate(http_method):
    def returned(self, *args, **kwargs):
        return self.request(http_method, *args, **kwargs)
    returned.__name__ = http_method
    returned.__doc__ = "Shortcut for :func:`.request({!r}) <API.request>`".format(http_method)
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
        self._approved = False
        self._session = None

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

    @contextmanager
    def get_unapproved_context(self):
        return self.get_approval_context(False)

    get = _get_request_delegate("get")
    put = _get_request_delegate("put")
    post = _get_request_delegate("post")
    patch = _get_request_delegate("patch")
    delete = _get_request_delegate("delete")

    def request(self, http_method, path, assert_success=True, **kwargs):
        """
        Sends a request to the IZBox API interface

        :rtype: :class:`.Response`
        """
        returned = None
        for url, attempted_session in self._iter_possible_http_sessions():
            full_url = _join_path(url, URL(path))
            if http_method in ['put', 'delete'] and self._approved:
                full_url = full_url.add_query_param('approved', 'true')
            hostname = full_url.hostname
            _logger.debug("{} <-- {} {}", hostname, http_method.upper(), full_url)
            if 'data' in kwargs:
                kwargs['data'] = json.dumps(kwargs.pop('data'))
                _logger.debug("{} <-- DATA: {}" , hostname, kwargs['data'])
            kwargs.setdefault('timeout', self._default_request_timeout)
            response = attempted_session.request(http_method, full_url, **kwargs)
            elapsed = response.elapsed.total_seconds()
            _logger.debug("{} --> {} {} (took {:.04f}s)", hostname, response.status_code, response.reason, elapsed)
            returned = Response(url, response)
            _logger.debug("{} --> {}", hostname, returned.get_json())
            if response.status_code != httplib.SERVICE_UNAVAILABLE:
                self._url = url
                self._session = attempted_session
                break

        if assert_success is not False:
            returned.assert_success()
        return returned

    _api_address_index = 0
    def _iter_possible_http_sessions(self):
        if self._session is not None:
            yield self._url, self._session

        addresses = list(self.system.get_api_addresses())
        for i in range(self._api_address_index, len(addresses)+self._api_address_index):
            i = i % len(addresses)
            self._api_address_index = i
            attempted = addresses[i]
            session = requests.Session()
            session.auth = self.system.get_api_auth()
            session.headers['content-type'] = 'application/json'
            url = URL("http://{}:{}".format(*attempted))
            url = url.add_path("api/rest")
            yield url, session


class Response(object):
    """
    IZBox API request response
    """
    def __init__(self, url, resp):
        super(Response, self).__init__()
        #: response object as returned from ``requests``
        self.response = resp
        #: URLObject of the final location the response was obtained from
        self.url = url

    def get_json(self):
        return self.response.json()

    def _get_result(self):
        return self.get_json()['result']

    def get_result(self):
        return self._get_result()

    def get_error(self):
        return self.get_json()['error']

    def __repr__(self):
        return repr(self.response)

    def get_metadata(self):
        return self.get_json()['metadata']

    def get_total_num_objects(self):
        return self.get_metadata()["number_of_objects"]

    def assert_success(self):
        try:
            self.response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise APICommandFailed(self.response, e)
# TODO : implement async request
