from ..core.api import APITarget, API
from ..core.type_binder_container import TypeBinderContainer
from .filesystem import Filesystem

class IZBox(APITarget):

    def __init__(self, address, auth=None):
        super(IZBox, self).__init__()
        self._address = address
        self.objects = TypeBinderContainer(self)
        if auth is None:
            # TODO: take from configuration
            auth = ("infinidat", "123456")
        self._auth = auth
        self.api = API(self)

        for object_type in [Filesystem]:
            self.objects.install(object_type)

    def get_api_address(self):
        return self._address

    def get_api_timeout(self):
        # TODO: take this from config
        return 60

    def get_api_auth(self):
        return self._auth

    def __repr__(self):
        return self._address[0]
