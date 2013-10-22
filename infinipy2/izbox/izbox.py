from ..core.api import APITarget, API
from ..core.type_binder_container import TypeBinderContainer
from .components import IZBoxSystemComponents
from .filesystem import Filesystem, Snapshot
from .events import Events

class IZBox(APITarget):

    def __init__(self, address, auth=None):
        """
        :param address: Either a tuple of (host, port), or a list of such tuples for multiple addresses
        """
        super(IZBox, self).__init__()
        if not isinstance(address[0], (list, tuple)):
            address = [address]
        self._addresses = address
        self.objects = TypeBinderContainer(self)
        if auth is None:
            # TODO: take from configuration
            auth = ("infinidat", "123456")
        self._auth = auth
        self.api = API(self)
        for object_type in [Filesystem, Snapshot]:
            self.objects.install(object_type)

        self.components = IZBoxSystemComponents(self)

        self.events = Events(self)

    def get_state(self):
        return self.components.system_component.get_state()

    def get_api_addresses(self):
        return self._addresses

    def get_api_timeout(self):
        # TODO: take this from config
        return 60

    def get_api_auth(self):
        return self._auth

    def __repr__(self):
        return self._addresses[0][0]
