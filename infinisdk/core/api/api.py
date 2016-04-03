from functools import partial
import flux
import json
import sys
import socket
from contextlib import contextmanager

import gossip
from logbook import Logger
from sentinels import NOTHING
from urlobject import URLObject as URL

import colorama

from ... import _compat
from ..._compat import httplib, iteritems, requests, RequestException, ProtocolError
from ..config import config
from ..exceptions import (APICommandFailed, APITransportFailure,
                          CommandNotApproved, SystemNotFoundException)
from ..utils import deprecated
from .special_values import translate_special_values


_RETRY_REQUESTS_EXCEPTION_TYPES = (RequestException, socket.error, ProtocolError)

_logger = Logger(__name__)

def _get_request_delegate(http_method):
    def returned(self, path, **kwargs):
        return self.request(http_method, path=path, **kwargs)
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


def _approval_preprocessor(approve, request):
    if request.method != "get" and not request.url.path.startswith("/api/internal/"):
        request.url = request.url.set_query_param('approved', str(approve).lower())


class API(object):

    def __init__(self, target, auth, use_ssl, ssl_cert):
        super(API, self).__init__()
        self._auth = None
        self._preprocessors = []
        self.system = target
        self._use_ssl = use_ssl
        self._ssl_cert = ssl_cert
        self._use_basic_auth = False
        self._check_version_compatibility = True
        self._default_request_timeout = None
        self._interactive = False
        self._auto_retry_predicates = {}
        self._session = None
        self.reinitialize_session(auth=auth)
        self._urls = [self._url_from_address(address, use_ssl) for address in target.get_api_addresses()]
        self._active_url = None
        self._checked_version = False
        self._no_reponse_logs = False
        self._use_pretty_json = config.root.api.log.pretty_json
        self._login_refresh_enabled = True

    @contextmanager
    def disabled_login_refresh_context(self):
        """Inside this context, InfiniSDK will not attempt to refresh login cookies
        when logged out by expired cookies
        """
        prev = self._login_refresh_enabled
        self._login_refresh_enabled = False
        try:
            yield
        finally:
            self._login_refresh_enabled = prev

    @contextmanager
    def disable_version_checking_context(self):
        prev = self._check_version_compatibility
        self._check_version_compatibility = False
        try:
            yield
        finally:
            self._check_version_compatibility = prev

    @contextmanager
    def use_basic_auth_context(self):
        """Causes API requests to send auth through Basic authorization
        """
        prev = self._use_basic_auth
        try:
            self._use_basic_auth = True
            yield
        finally:
            self._use_basic_auth = prev


    def reinitialize_session(self, auth=None):
        prev_auth = self._auth
        if auth is None:
            auth = self._auth
        if self._session is not None:
            prev_cookies = self._session.cookies.copy()
        else:
            prev_cookies = None
        self._session = requests.Session()

        assert self._session.cert is None
        self._session.cert = self._ssl_cert
        if not self._ssl_cert:
            self._session.verify = False
        self.set_auth(auth, login=False)

        if prev_auth == auth and prev_cookies is not None:
            self._session.cookies.update(prev_cookies)


    @property
    def urls(self):
        return list(self._urls)

    @property
    def url(self):
        if not self._urls:
            raise RuntimeError('No URLs configured for {0}'.format(self.system))
        return self._urls[0]

    @contextmanager
    def query_preprocessor(self, preprocessor):
        self._preprocessors.append(preprocessor)
        try:
            yield
        finally:
            self._preprocessors.remove(preprocessor)

    @contextmanager
    def get_approval_context(self, value):
        """A context manager that controls whether requests are automatically approved (confirmed)
        """
        with self.query_preprocessor(partial(_approval_preprocessor, value)):
            yield

    def get_approved_context(self):
        """A context marking all operations as approved (confirmed)"""
        return self.get_approval_context(True)

    def get_unapproved_context(self):
        """A context marking all operations as unapproved (not confirmed)"""
        return self.get_approval_context(False)

    def set_source_identifier(self, identifier):
        self._session.headers["User-Agent"] = identifier

    def set_interactive_approval(self):
        """Causes an interactive prompt whenever a command requires approval from the user"""
        self._interactive = True

    @contextmanager
    def change_request_default_timeout_context(self, timeout):
        prev = self.get_request_default_timeout()
        self.set_request_default_timeout(timeout)
        try:
            yield
        finally:
            self.set_request_default_timeout(prev)

    def get_request_default_timeout(self):
        return self._default_request_timeout

    def set_request_default_timeout(self, timeout_seconds):
        self._default_request_timeout = timeout_seconds

    def set_auth(self, username_or_auth, password=NOTHING, login=True):
        """
        Sets the username and password under which operations will be performed

        Can be used both with a tuple argument or with two arguments (username, password):

        >>> system.api.set_auth(('username', 'password'))
        >>> system.api.set_auth('username', 'password')
        """
        if username_or_auth is None and password is NOTHING:
            self._auth = None
            password = None
        else:
            if isinstance(username_or_auth, tuple):
                if password is not NOTHING:
                    raise TypeError("Auth given as tuple, but password was used")
                username, password = username_or_auth
            else:
                if password is NOTHING:
                    raise TypeError("Password not specified")
                username = username_or_auth
            self._auth = (username, password)
        self.clear_cookies()
        if login:
            self.system.login()

    def get_auth(self):
        """
        Returns a tuple of the current username/password used by the API
        """
        return self._auth

    @contextmanager
    def get_auth_context(self, username, password, login=True):
        """
        Changes the API authentication information for the duration of the context:

        >>> with system.api.get_auth_context('username', 'password'):
        ...     ... # execute operations as 'username'
        """
        _logger.debug('Changing credentials to {}', username)
        auth = (username, password)
        prev = self.get_auth()
        prev_cookies = self._session.cookies.copy()
        self.clear_cookies()
        try:
            self.set_auth(*auth, login=login)
            yield
        finally:
            _logger.debug('Changing credentials back to {[0]}', prev)
            self.set_auth(*prev, login=False)
            _logger.trace('Restoring cookies for user: {}', prev_cookies)
            self._session.cookies.clear()
            self._session.cookies.update(prev_cookies)


    def clear_cookies(self):
        _logger.trace('Clearing cookies: {}', self._session.cookies)
        self._session.cookies.clear()


    @deprecated(message="Use get_auth_context instead")
    def auth_context(self, *args, **kwargs):
        return self.get_auth_context(*args, **kwargs)

    get = _get_request_delegate("get")
    put = _get_request_delegate("put")
    post = _get_request_delegate("post")
    patch = _get_request_delegate("patch")
    delete = _get_request_delegate("delete")

    def _request(self, http_method, path, assert_success=True, **kwargs):
        """
        Sends a request to the system API interface

        :returns: :class:`.Response`
        """
        check_version = kwargs.pop("check_version", True)
        if check_version and self._check_version_compatibility and not self._checked_version and config.root.check_version_compatibility:
            self._checked_version = True
            try:
                with self.use_basic_auth_context():
                    self.system.check_version()
            except:
                self._checked_version = False
                raise

        returned = None
        kwargs.setdefault("timeout", self._default_request_timeout)
        auth = None

        if hasattr(self.system, 'compat'):
            if path != '_features':
                if not self.system.compat.is_initialized():
                    with self.disable_version_checking_context():
                        self.system.compat.initialize()
            if self._use_basic_auth or not self.system.compat.is_initialized() or not self.system.compat.has_auth_sessions():
                auth = self._auth

        raw_data = kwargs.pop("raw_data", False)
        data = kwargs.pop("data", NOTHING)
        sent_json_object = None
        headers = kwargs.pop('headers', None)
        if headers is None:
            headers = {}
        else:
            headers = headers.copy()

        if data is not NOTHING:
            headers['Content-type'] = 'application/json'
            if raw_data:
                sent_json_object = data
            else:
                data = translate_special_values(data)
                sent_json_object = data
                data = json.dumps(data)
        else:
            assert raw_data is False, "Cannot handle raw_data with no data"

        url_params = kwargs.pop('params', None)
        if url_params is not None:
            url_params = translate_special_values(url_params)

        specified_address = kwargs.pop("address", None)
        urls = self._get_possible_urls(specified_address)

        for url in urls:
            full_url = _join_path(url, URL(path))

            if http_method != "get" and not self._interactive and not path.startswith("/api/internal/"):
                full_url = self._with_approved(full_url)

            hostname = full_url.hostname
            api_request = requests.Request(http_method, full_url, data=data if data is not NOTHING else None, params=url_params, headers=headers, auth=auth)
            for preprocessor in self._preprocessors:
                preprocessor(api_request)


            _logger.trace("{0} <-- {1} {2}", hostname, http_method.upper(), api_request.url)
            if data is not NOTHING:
                if data != api_request.data:
                    sent_json_object = json.loads(api_request.data)
                self._log_sent_data(hostname, data, sent_json_object)

            prepared = self._session.prepare_request(api_request)
            gossip.trigger('infinidat.sdk.before_api_request', request=prepared)
            start_time = flux.current_timeline.time()
            try:
                response = self._session.send(prepared, **kwargs)
            except Exception as e:
                e.api_request_obj = api_request
                raise
            end_time = flux.current_timeline.time()
            gossip.trigger('infinidat.sdk.after_api_request', request=prepared, response=response)
            response.start_time = start_time
            response.end_time = end_time

            elapsed = response.elapsed.total_seconds()
            _logger.trace("{0} --> {1} {2} (took {3:.04f}s)", hostname, response.status_code, response.reason, elapsed)
            returned = Response(response, data)
            resp_data = returned.get_json()
            if self._no_reponse_logs:
                logged_response_data = "..."
            elif self._use_pretty_json and resp_data is not None:
                logged_response_data = json.dumps(resp_data, indent=4, separators=(',', ': '))
            else:
                logged_response_data = resp_data
            _logger.trace("{0} --> {1}", hostname, logged_response_data)
            if response.status_code != httplib.SERVICE_UNAVAILABLE:
                if specified_address is None: # need to remember our next API target
                    self._active_url = url
                break
        return returned

    def _log_sent_data(self, hostname, data, sent_json_object):
        try:
            # Hide potential passwords included in JSON
            if isinstance(sent_json_object, dict) and 'password' in sent_json_object:
                data = json.dumps(
                    dict(sent_json_object, password='*' * len(sent_json_object['password']))
                    )
        except Exception:
            pass
        _logger.trace("{0} <-- DATA: {1}" , hostname, data)

    @contextmanager
    def get_no_response_logs_context(self):
        prev = self._no_reponse_logs
        self._no_reponse_logs = True
        try:
            yield
        finally:
            self._no_reponse_logs = prev

    @deprecated(message="Use get_no_response_logs_context instead")
    def no_response_logs_context(self):
        return self.get_no_response_logs_context()

    def add_auto_retry(self, retry_predicate, max_retries=1, sleep_seconds=None):
        if sleep_seconds is None: # backwards compatibility
            sleep_seconds = config.root.defaults.retry_sleep_seconds
        assert retry_predicate not in self._auto_retry_predicates
        _logger.debug("Add auto-retry predicate {0} for {1} retries", retry_predicate, max_retries)
        self._auto_retry_predicates[retry_predicate] = (max_retries, sleep_seconds)

    def remove_auto_retry(self, retry_predicate):
        _logger.debug("Remove auto-retry predicate {0}", retry_predicate)
        del self._auto_retry_predicates[retry_predicate]

    def is_auto_retry_active(self, retry_predicate):
        return retry_predicate in self._auto_retry_predicates

    def _get_auto_retries_context(self):
        return _AutoRetryContext(self._auto_retry_predicates)

    def set_cookie(self, cookie, value):
        self._session.cookies[cookie] = value

    def get_cookie(self, cookie):
        return self._session.cookies[cookie]

    def delete_cookie(self, cookie):
        del self._session.cookies[cookie]

    def request(self, http_method, path, assert_success=True, **kwargs):
        """Sends HTTP API request to the remote system
        """
        did_interactive_confirmation = False
        did_login = False
        had_cookies = bool(self._session.cookies)
        auto_retries_context = self._get_auto_retries_context()
        while True:
            with auto_retries_context:
                try:
                    returned = self._request(http_method, path, **kwargs)
                except _RETRY_REQUESTS_EXCEPTION_TYPES as e:
                    request_kwargs = dict(url=path, method=http_method, **kwargs)
                    _logger.debug('Exception while sending API command to {0}: {1}', self.system, e)
                    error_str = str(e)
                    if 'gaierror' in error_str or 'nodename nor servname' in error_str or \
                       'Name or service not known' in error_str:
                        raise SystemNotFoundException(e)
                    raise APITransportFailure(self.system, request_kwargs, e)

                if returned.status_code == requests.codes.unauthorized and \
                   self._login_refresh_enabled and \
                   had_cookies and \
                   not did_login and \
                   'login' not in path:

                    _logger.trace('Performing login again due to expired cookie ({})', self._session.cookies)
                    self.system.mark_not_logged_in()
                    self.system.login()
                    did_login = True
                    continue

                if assert_success:
                    try:
                        returned.assert_success()
                    except APICommandFailed as e:
                        if self._is_approval_required(e):
                            reason = self._get_unapproved_reason(e.response.response.json())
                            if self._interactive and not did_interactive_confirmation:
                                did_interactive_confirmation = True
                                if self._ask_approval_interactively(http_method, path, reason):
                                    path = self._with_approved(path)
                                    continue
                                raise CommandNotApproved(e.response, reason)
                        raise
                return returned
        assert False, "Should never get here!"

    def _with_approved(self, path):
        return path.set_query_param('approved', 'true')

    def _ask_approval_interactively(self, method, path, reason):
        if not reason:
            reason = "API operation requires approval: {0} {1}".format(method, path)
        msg = "{0} Approve? [y/N] ".format(reason)
        if sys.stdout.isatty():
            msg = colorama.Fore.YELLOW + msg + colorama.Fore.RESET
        # note: call through module to allow stubbing
        return _compat.raw_input(msg).strip().lower() in ['yes', 'y']

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
    def __init__(self, resp, data):
        super(Response, self).__init__()
        self.method = resp.request.method
        #: Response object as returned from ``requests``
        self.response = resp
        #: URLObject of the final location the response was obtained from
        self.url = URL(resp.request.url)
        #: Data sent to on
        self.sent_data = data
        self._cached_json = NOTHING

    @property
    def status_code(self):
        return self.response.status_code

    def get_json(self):
        """
        :returns: The JSON object returned from the system, or None if no json could be decoded
        """
        returned = self._cached_json
        if returned is NOTHING:
            try:
                returned = self.response.json()
            except (ValueError, TypeError):
                returned = None
            self._cached_json = returned
        return returned

    def _get_result(self):
        return self.get_json()["result"]

    def get_result(self):
        """
        :returns: The result of the API call, extracted from the response JSON object
        """
        return self._get_result()

    def get_error(self):
        """
        :returns: The error portion of the response as returned from the system, or None if it doesn't exist
        """
        json = self.get_json()
        if json is not None:
            return json["error"]

    def __repr__(self):
        return repr(self.response)

    def get_metadata(self):
        """
        :returns: The metadata portion of the response (paging information, etc.) as returned from the system, or None
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
            if self.sent_data is not NOTHING  and self.sent_data and 'password' in self.sent_data:
                self.sent_data = '<HIDDEN>'
            raise APICommandFailed.raise_from_response(self)


class _AutoRetryContext(object):
    def __init__(self, global_retries_dict):
        self._retries_dict = None
        self._global_retries_dict = global_retries_dict

    def _should_retry_request(self, exc):
        if self._retries_dict is None:
            self._retries_dict = dict((k, v[0]) for k, v in self._global_retries_dict.items())
        for retry_predicate, retries_left in iteritems(self._retries_dict):
            if retries_left < 1:
                return None
            if retry_predicate(exc):
                max_retries, retry_sleep_seconds = self._global_retries_dict[retry_predicate]
                retried_count = max_retries - retries_left + 1
                _logger.debug("Auto retry API ({0} of {1}) by {2}: {3}",
                        retried_count, max_retries, retry_predicate, exc)
                self._retries_dict[retry_predicate] -= 1
                return retry_sleep_seconds
        return None

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        sleep_seconds = self._should_retry_request(exc_value)
        if sleep_seconds is not None:
            flux.current_timeline.sleep(sleep_seconds)
            return True
        return None

# TODO : implement async request
