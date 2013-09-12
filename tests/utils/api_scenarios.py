from contextlib import contextmanager
from infinipy2._compat import httplib
from sentinels import NOTHING
import functools
import httpretty
import json
import os
import requests
import yaml

from urlobject import URLObject as URL

def iter_api_scenario(filename):
    if not os.path.isfile(filename):
        if not filename.endswith(".yml"):
            filename = filename + ".yml"
        filename = os.path.join(os.path.dirname(__file__), "_api_scenarios", filename)
    with open(filename) as infile:
        for rule in yaml.load_all(infile):
            yield Rule.from_yaml(rule)

@contextmanager
def api_scenario(name, target):
    httpretty.enable()
    try:
        for rule in iter_api_scenario(name):
            rule.register(target)
        yield
    finally:
        httpretty.disable()

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

    def register(self, target):
        url = URL("http://{}:{}".format(*target.get_api_address())).add_path(self.request.path)
        httpretty.register_uri(
            method=getattr(httpretty, self.request.method.upper()), uri=url,
            body=json.dumps(self.response.data), **self.response.headers)

class Request(object):
    def __init__(self, method, path, data=NOTHING):
        super(Request, self).__init__()
        self.method = method
        self.path = path
        self.data = data

    @classmethod
    def from_yaml(cls, yaml):
        if isinstance(yaml, str):
            method, path = yaml.split()
            yaml = {"method": method, "path": path}
        return cls(**yaml)

    def send(self, url, **kwargs):
        url = url.add_path(self.path)
        headers = {}
        data = self.data
        if data is not NOTHING:
            headers["Content-type"] = "application/json"
            data = json.dumps(data)
        else:
            data = None
        return getattr(requests, self.method.lower())(
            url, headers=headers, data=data, **kwargs)

    def __rshift__(self, response):
        return Rule(self, response)

class Response(object):
    def __init__(self, status_code=httplib.OK, data="", headers=None):
        super(Response, self).__init__()
        self.status_code = status_code
        self.data = data
        self.headers = headers or {}

    @classmethod
    def from_yaml(cls, yaml):
        if not yaml:
            return None
        headers = yaml["headers"] = yaml.get("headers", {})
        if "json" in yaml:
            assert "data" not in yaml
            yaml["data"] = yaml.pop("json")
            headers["Content-type"] = "application/json"
        return cls(**yaml)
