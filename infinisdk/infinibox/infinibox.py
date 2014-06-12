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
        return type(address).__name__ == "Infinibox"

    def _get_simulator_address(self, address):
        simulator_address = address.get_floating_addresses()[0]
        return (simulator_address, 80)

    def get_approval_failure_codes(self):
        d = config.get_path('infinibox.approval_required_codes')
        return d

    def get_state(self):
        return self.components.system_component.get_state()

    def is_simulator(self):
        return "simulator" in self.get_name()

    def is_mock(self):
        return "mock" in self.get_name()

    def get_system_info(self, field_name):
        return self.components.system_component.get_field(field_name,
                                                          from_cache=True,
                                                          fetch_if_not_cached=True)

    def get_name(self):
        """
        Returns the name of the system
        """
        return self.get_system_info('name')

    def get_serial(self):
        """
        Returns the serial number of the system
        """
        return self.get_system_info('serial_number')

    def get_version(self):
        """
        Returns the product version of the system
        """
        return self.get_system_info('version')
