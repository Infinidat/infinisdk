from infi.unittest import TestCase
from .api_scenarios import api_scenario
from infinipy2.core import *
from infinipy2.core.api import APITarget, API

class FakeSystem(APITarget):
    _ADDRESS = ("fakeaddress", 80)
    _AUTH = ("fakeuser", "fakepassword")

    def __init__(self):
        super(FakeSystem, self).__init__()
        self.api = API(self)

    def get_api_timeout(self):
        return 1

    def get_api_address(self):
        return self._ADDRESS

    def get_api_auth(self):
        return self._AUTH

    _ctx = None
    def start_api_scenario(self, name):
        assert self._ctx is None
        self._ctx = api_scenario(name, self)
        self._ctx.__enter__()

    def end_api_scenario(self):
        self._ctx.__exit__(None, None, None)
