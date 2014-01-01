from ..core.api import APITarget
from ..core.config import config
from .components import InfiniBoxSystemComponents
from .events import Events, EmailRule
from .volume import Volume
from .pool import Pool
from .host import Host
from .cluster import Cluster
from .user import User


class InfiniBox(APITarget):
    OBJECT_TYPES = [Volume, Pool, Host, Cluster, User, EmailRule]
    SYSTEM_EVENTS_TYPE = Events
    SYSTEM_COMPONENTS_TYPE = InfiniBoxSystemComponents

    def _get_api_auth(self):
        d = config.get_path('infinibox.defaults.system_api')
        return (d['username'], d['password'])

    def _get_api_timeout(self):
        return config.get_path('infinibox.defaults.system_api.timeout_seconds')

    def _is_simulator(self, address):
        return False  # TODO: Implement!! (and add _get_simulator_address method)

    def get_state(self):
        return self.components.system_component.get_state()

    def is_simulator(self):
        raise NotImplementedError()

    def is_mock(self):
        raise NotImplementedError()

    def get_system_info(self, field_name):
        return self.components.system_component.get_field(field_name,
                                                          from_cache=True,
                                                          fetch_if_not_cached=True)

    def get_name(self):
        return self.get_system_info('name')

    def get_serial(self):
        return self.get_system_info('serial_number')

    def get_version(self):
        return self.get_system_info('version')
