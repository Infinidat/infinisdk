import requests, json
from urlobject import URLObject as URL
from logbook import Logger
from contextlib import contextmanager
import types
from ..exceptions import APICommandFailed

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
        self._reset_session()

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

    def _reset_session(self):
        self._session = requests.Session()
        self._session.auth = self.system.get_api_auth()
        self._session.headers['content-type'] = 'application/json'
        url = URL("http://{}:{}".format(*self.system.get_api_address()))
        self._url = url.add_path("api/rest")

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
        _url = URL(path)
        full_url = _join_path(self._url, _url)
        if http_method in ['put', 'delete'] and self._approved:
            full_url = full_url.add_query_param('approved', 'true')
        hostname = full_url.hostname
        _logger.debug("{} <-- {} {}", hostname, http_method.upper(), full_url)
        if 'data' in kwargs:
            raw_data = update_request_data(kwargs.pop('data'))
            kwargs['data'] = json.dumps(raw_data)
            _logger.debug("{} <-- DATA: {}" , hostname, kwargs['data'])
        kwargs.setdefault('timeout', self._default_request_timeout)
        response = self._session.request(http_method, full_url, **kwargs)
        elapsed = response.elapsed.total_seconds()
        _logger.debug("{} --> {} {} (took {:.04f}s)", hostname, response.status_code, response.reason, elapsed)
        returned = Response(response)
        _logger.debug("{} --> {}", hostname, returned.get_json())
        if assert_success is not False:
            returned.assert_success()
        return returned

class Response(object):
    """
        IZBox API request response 
    """
    def __init__(self, resp):
        super(Response, self).__init__()
        self.response = resp
    def get_json(self):
        return self.response.json()
    def _get_result(self):
        return self.get_json()['result']
    def get_result(self):
        result = self._get_result()
        return update_response_data(result)
    def get_error(self):
        return self.get_json()['error']
    def get_metadata(self):
        return self.get_json()['metadata']
    def assert_success(self):
        try:
            self.response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise APICommandFailed(self.response, e)
# TODO : implement async request
 
