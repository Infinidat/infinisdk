from ..core.system_object import APICommandFailed, APITransportFailure
from infi.pyutils.functors import PASS

import functools
import waiting
from contextlib import contextmanager
from logbook import Logger

_logger = Logger(__name__)

class InfiniboxCluster(object):
    """Manages higher-level operations relating to the clustered nature of the system
    """

    def __init__(self, system):
        super(InfiniboxCluster, self).__init__()
        self.system = system

    def _get_service_by_role(self, name, role):
        return self.system.components.services.get(name=name.lower(), role=role.upper())

    def get_core_master(self):
        return self._get_service_by_role('CORE', 'MASTER')

    def get_core_secondary(self):
        return self._get_service_by_role('CORE', 'SECONDARY')

    def get_management_master(self):
        return self._get_service_by_role('MGMT', 'MASTER')

    def get_management_secondary(self):
        return self._get_service_by_role('MGMT', 'SECONDARY')

    def service_going_down_context(self, node, service_name):
        if service_name == 'mgmt2':
            return self.possible_management_take_over_context(node)
        return PASS

    @contextmanager
    def possible_management_take_over_context(self, node):
        management_service = node.get_management_service()
        if management_service.is_active() and management_service.is_master():
            management_secondary = self.get_management_secondary()
            yield
            self.wait_for_management_takeover(management_secondary)
        else:
            yield

    def wait_for_management_takeover(self, new_management_master, deadline=300):
        """During the management takeover there's a time windows (as defined in config), in which we allow API failures
        """
        _logger.info("Waiting for {} to become management master. deadline is {}", new_management_master, deadline)
        waiting.wait(functools.partial(self.safe_is_management_cluster_master, new_management_master), timeout_seconds=deadline, sleep_seconds=5)

    @staticmethod
    def safe_is_management_cluster_master(management_service):
        """Safe check if management is master, to handle the management master takeover
        """
        assert management_service.get_node().get_management_service() == management_service, \
            "{} is expected to be management service".format(management_service)
        result = False
        try:
            result = management_service.is_master()
        except (APICommandFailed, APITransportFailure):
            pass
        return result
