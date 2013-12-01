from ..core.api import APITarget, API
from ..core.type_binder_container import TypeBinderContainer
from .components import IZBoxSystemComponents
from .filesystem import Filesystem, Snapshot
from .user import User
from .events import Events, PushRule

class IZBox(APITarget):

    def __init__(self, address, auth=None):
        """
        :param address: Either a tuple of (host, port), or a list of such tuples for multiple addresses
        """
        super(IZBox, self).__init__()
        if type(address).__name__ == "Simulator":
            address = (address.base_url.netloc.hostname, address.base_url.netloc.port or 80)
        if not isinstance(address[0], (list, tuple)):
            address = [address]
        self._addresses = self._normalize_addresses(address)
        self.objects = TypeBinderContainer(self)
        if auth is None:
            # TODO: take from configuration
            auth = ("infinidat", "123456")
        self._auth = auth
        self.api = API(self)
        for object_type in [Filesystem, Snapshot, User, PushRule]:
            self.objects.install(object_type)

        self.components = IZBoxSystemComponents(self)

        self.events = Events(self)

    def _normalize_addresses(self, addresses):
        returned = []
        for address in addresses:
            if not isinstance(address, tuple):
                address = (address, 80)
            if len(address) != 2:
                raise ValueError("Invalid address specified: {!r}".format(address))
            returned.append(address)
        return returned

    def get_state(self):
        return self.components.system_component.get_state()

    def get_api_addresses(self):
        return self._addresses

    def is_simulator(self):
        return "izsim" in self.get_name()

    def is_mock(self):
        return "mock" in self.get_name()

    def is_virtual(self):
        return all([self.get_serial() > 35000, not self.is_mock()])

    def get_name(self):
        return self.get_system_info()["name"]

    def get_serial(self):
        return self.get_system_info()["system_serial"]

    def get_version(self):
        return self.get_system_info()["version"]

    def get_model(self):
        return "G3200"

    def get_system_info(self):
        data = self.components.system_component.get_field("data", from_cache=True, fetch_if_not_cached=True)
        return data

    def get_api_timeout(self):
        # TODO: take this from config
        return 60

    def get_api_auth(self):
        return self._auth

    def __repr__(self):
        return self._addresses[0][0]
