from contextlib import contextmanager
from infinipy2._compat import httplib
from sentinels import NOTHING
from urlobject import URLObject as URL
import functools
import json
import os
import requests
import yaml
import logbook

_logger = logbook.Logger(__name__)

from urlobject import URLObject as URL

def get_real_scenario_filename(filename):
    if not os.path.isfile(filename):
        if not filename.endswith(".yml"):
            filename = filename + ".yml"
        filename = os.path.join(os.path.dirname(__file__), "_api_scenarios", filename)
    return filename

def iter_api_scenario(filename):
    filename = get_real_scenario_filename(filename)
    with open(filename) as infile:
        for rule in yaml.load_all(infile):
            yield Rule.from_yaml(rule)

@contextmanager
def api_scenario(name, target):
    old_request = requests.sessions.Session.request
    requests.sessions.Session.request = RequestHandler(target, list(iter_api_scenario(name)))
    try:
        yield
    finally:
        requests.sessions.Session.request = old_request

class RequestHandler(object):
    def __init__(self, target, rules):
        super(RequestHandler, self).__init__()
        self._rules = rules
        self._address = target.get_api_address()

    def __call__(self, method, url, *args, **kwargs):
        _logger.debug("Handling request: {} {} {} {}", method, url, args, kwargs)
        url = URL(url)
        if (url.hostname, url.port) != self._address:
            raise InvalidRequas("Request {} {} does not match hostname/port of target".format(method, url))
        for rule in self._rules:
            if rule.request.method != method:
                _logger.debug("{} does not match (wrong method)", rule)
                continue
            assert rule.request.path.startswith("/")
            rule_url = URL("http://{}:{}".format(*self._address) + rule.request.path)
            if rule_url != url:
                _logger.debug("{} does not match (wrong url {})", rule, rule_url)
                continue
            return rule.response.make_response()
        raise InvalidRequest("Could not find matching rule for {} {}".format(method, url))

class InvalidRequest(Exception):
    pass

class Rule(object):
    def __init__(self, request, response):
        super(Rule, self).__init__()
        self.request = request
        self.response = response

    @classmethod
    def from_yaml(cls, yaml):
        returned = cls(
            Request.from_yaml(yaml["request"]),
            Response.from_yaml(yaml.get("response", None))
        )
        returned.original_yaml = yaml
        return returned

    def get_url(self, target):
        return URL("http://{}:{}".format(*target.get_api_address())).add_path(self.request.path)

    def __repr__(self):
        return "<Rule {} --> {}>".format(URL("http://SERVER") + self.request.path, self.response.status_code)

UNSPECIFIED = object()

class Request(object):
    def __init__(self, method, path, data=NOTHING, headers=UNSPECIFIED):
        super(Request, self).__init__()
        self.method = method.lower()
        self.path = path
        self.data = data
        self.headers = headers

    @classmethod
    def from_yaml(cls, yaml):
        if isinstance(yaml, str):
            method, path = yaml.split()
            yaml = {"method": method, "path": path}
        return cls(**yaml)

    def get_as_dict(self, root_url, **overrides):
        assert self.path.startswith("/") and not root_url.endswith("/")
        url = root_url + self.path
        headers = overrides.pop("headers", {}).copy()
        data = self.data
        if data is not NOTHING:
            headers["Content-type"] = "application/json"
            data = json.dumps(data)
        else:
            data = None
        returned = {"url": url, "headers": headers, "data": data, "method": self.method}
        returned.update(overrides)
        return returned

    def send(self, url, **kwargs):
        as_dict = self.get_as_dict(url, **kwargs)
        return requests.request(**as_dict)

    def __rshift__(self, response):
        return Rule(self, response)

class Response(object):
    def __init__(self, status_code=httplib.OK, content="", headers=None):
        super(Response, self).__init__()
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        if isinstance(content, (dict, list)):
            if "Content-type" not in self.headers:
                self.headers["Content-type"] = "application/json"
            self.content = json.dumps(self.content)

    def get_as_dict(self):
        return {"status_code": self.status_code, "content": self.content, "headers": self.headers}

    def make_response(self):
        returned = requests.Response()
        returned.status_code = self.status_code
        returned._content = self.content.encode("utf-8")
        returned.headers.update(self.headers)
        return returned

    @classmethod
    def from_yaml(cls, yaml):
        if not yaml:
            return None
        headers = yaml["headers"] = yaml.get("headers", {})
        if "json" in yaml:
            assert "content" not in yaml
            yaml["content"] = yaml.pop("json")
            headers["Content-type"] = "application/json"
        return cls(**yaml)
