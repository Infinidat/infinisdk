import functools
from infinipy2._compat import httplib
import httpretty
import json

from urlobject import URLObject as URL

class Rules(object):
    def __init__(self, *rules):
        super(Rules, self).__init__()
        self.rules = list(rules)

    def __call__(self, target):
        return BoundRules(self.rules, target)

class BoundRules(object):
    def __init__(self, rules, target):
        super(BoundRules, self).__init__()
        self.rules = rules
        self.target = target

    def __enter__(self):
        httpretty.enable()
        try:
            for rule in self.rules:
                rule.register(self.target)
        except:
            httpretty.disable()
            raise

    def __exit__(self, *_):
        httpretty.disable()

class Rule(object):
    def __init__(self, request, response):
        super(Rule, self).__init__()
        self.request = request
        self.response = response

    def register(self, target):
        url = URL("http://{}:{}".format(*target.get_api_address())).add_path(self.request.path)
        httpretty.register_uri(
            method=getattr(httpretty, self.request.method.upper()), uri=url,
            body=self.response.data, **self.response.headers)

class Request(object):
    def __init__(self, method, path):
        super(Request, self).__init__()
        self.method = method
        self.path = path

    def __rshift__(self, response):
        return Rule(self, response)

class Response(object):
    def __init__(self, status=httplib.OK, data="", headers=None):
        super(Response, self).__init__()
        self.status = status
        self.data = data
        self.headers = headers or {}

GET = functools.partial(Request, "get")
POST = functools.partial(Request, "post")

def OK(resp):
    resp.status = httplib.OK
    return resp

def JSON(data):
    return Response(data=json.dumps(data), headers={"Content-type": "application/json"})
