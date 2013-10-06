from infinipy2._compat import httplib
from urlobject import URLObject as URL
from json import dumps as encode_json, loads as decode_json
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

class api_scenario(object):
    def __init__(self, target, *scenarios):
        self.target = target
        self.scenarios = scenarios

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.end()

    def start(self):
        self.old_request = requests.sessions.Session.request
        requests.sessions.Session.request = RequestHandler(self.target, list(item for scenario in self.scenarios for item in iter_api_scenario(scenario)))

    def end(self):
        requests.sessions.Session.request = self.old_request
        self.old_request = None

class RequestHandler(object):
    def __init__(self, target, rules):
        super(RequestHandler, self).__init__()
        self._rules = rules
        self._address = target.get_api_address()

    def __call__(self, method, url, **kwargs):
        _logger.debug("Handling request: {} {} {}", method, url, kwargs)
        data = json = kwargs.pop("data", None)
        if data is not None:
            json = decode_json(data)
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
            if rule.request.json != json:
                _logger.debug("{} does not match (wrong data):\n{}", rule, LazyDiff(rule.request.json, json))
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
        return "<Rule {} {} --> {}>".format(self.request.method, URL("http://SERVER") + self.request.path, self.response.status_code)

class Request(object):
    def __init__(self, method, path, data=None, headers=None, json=None):
        super(Request, self).__init__()
        self.method = method.lower()
        if headers is None:
            headers = {}
        self.headers = headers
        self.json = json
        if json is not None:
            assert data is None
            data = encode_json(json)
            self.headers["Content-type"] = "application/json"
        self.data = data
        self.path = path
        self.headers = headers

    @classmethod
    def from_yaml(cls, yaml):
        if isinstance(yaml, str):
            method, path = yaml.split()
            yaml = {"method": method, "path": path}
        else:
            yaml = yaml.copy()
        return cls(**yaml)

    def get_as_dict(self, root_url, **overrides):
        assert self.path.startswith("/") and not root_url.endswith("/")
        url = root_url + self.path
        headers = self.headers
        if headers is UNSPECIFIED:
            headers = {}
        headers.update(overrides.pop("headers", {}))
        returned = {"url": url, "headers": headers, "data": self.data, "method": self.method}
        returned.update(overrides)
        return returned

    def send(self, url, **kwargs):
        as_dict = self.get_as_dict(url, **kwargs)
        import ipdb
        ipdb.set_trace()
        return requests.request(**as_dict)

class Response(object):
    def __init__(self, status_code=httplib.OK, content="", headers=None):
        super(Response, self).__init__()
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        if isinstance(content, (dict, list)):
            if "Content-type" not in self.headers:
                self.headers["Content-type"] = "application/json"
            self.content = encode_json(self.content)

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

class LazyDiff(object):
    __slots__ = ["a", "b"]
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def __repr__(self):
        diff = []
        for key in set(self.a) | set(self.b):
            a_value = self.a.get(key, "<<NOTHING>>")
            b_value = self.b.get(key, "<<NOTHING>>")
            if a_value != b_value:
                diff.append((key, a_value, b_value))

        return "\n".join("{!r}: {} != {}".format(*x) for x in diff)
        return "\n".join(":".join(*l) for l in dictdiffer.diff(self.a, self.b))
