from ..core.api import APITarget
from ..core.config import config
from .components import InfiniBoxSystemComponents
from .volume import Volume
from .pool import Pool


class InfiniBox(APITarget):
    OBJECT_TYPES = [Volume, Pool]
    # FIXME: Should have also:
    # Cluster & Host,
    # Events,
    # User
    # EmailRule,
    SYSTEM_COMPONENTS_TYPE = InfiniBoxSystemComponents

    def _get_api_auth(self):
        d = config.get_path('infinibox.defaults.system_api')
        return (d['username'], d['password'])

    def _get_api_timeout(self):
        return config.get_path('infinibox.defaults.system_api.timeout_seconds')

    def _is_simulator(self, address):
        return False  # TODO: Implement!! (and add _get_simulator_address method)
