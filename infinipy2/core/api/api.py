import json
from contextlib import contextmanager

import requests
from logbook import Logger

from .special_values import translate_special_values
from ..._compat import httplib
from ..exceptions import APICommandFailed, CommandNotApproved
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
        self._approved = True
        self._session = None
        self._session = requests.Session()
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
        kwargs.setdefault("timeout", self._default_request_timeout)
        data = kwargs.get("data")
        if data is not None:
            data = json.dumps(translate_special_values(kwargs.pop("data")))

        specified_address = kwargs.pop("address", None)
        urls = self._get_possible_urls(specified_address)

        for url in urls:
            full_url = _join_path(url, URL(path))
            # TODO: make approved deduction smarter
            if http_method != "get" and self._approved and not path.startswith("/api/internal/"):
                full_url = full_url.add_query_param("approved", "true")
            hostname = full_url.hostname
            _logger.debug("{} <-- {} {}", hostname, http_method.upper(), full_url)
            if data is not None:
                _logger.debug("{} <-- DATA: {}" , hostname, data)
            response = self._session.request(http_method, full_url, data=data, **kwargs)
            elapsed = response.elapsed.total_seconds()
            _logger.debug("{} --> {} {} (took {:.04f}s)", hostname, response.status_code, response.reason, elapsed)
            returned = Response(http_method, full_url, data, response)
            _logger.debug("{} --> {}", hostname, returned.get_json())
            if response.status_code != httplib.SERVICE_UNAVAILABLE:
                if specified_address is None: # need to remember our next API target
                    self._active_url = url
                break

        if assert_success:
            returned.assert_success()
        return returned

    def _get_possible_urls(self, address=None):

        if address is not None:
            return [self._url_from_address(address)]

        if self._active_url is not None:
            return [self._active_url]

        return self._urls

    def _url_from_address(self, address):
        return URL("http://{}:{}".format(*address)).add_path("/api/rest")


class Response(object):
    """
    IZBox API request response
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
            if self.response.status_code == httplib.FORBIDDEN:
                raise CommandNotApproved(self.response)
            raise APICommandFailed(self)

# TODO : implement async request
