###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
import itertools

from sentinels import NOTHING

from ..core.api import APITarget
from ..core.config import config, get_ini_option
from ..core.exceptions import VersionNotSupported
from .host_cluster import HostCluster

from .components import InfiniBoxSystemComponents
from .events import EmailRule, Events
from .host import Host
from infinisdk.core.utils import deprecated
from .pool import Pool
from .user import User
from .volume import Volume
from .filesystem import Filesystem
from .export import Export
from .network_space import NetworkSpace
from .network_interface import NetworkInterface

try:
    from infinisim.core.context import lookup_simulator_by_address
except ImportError:
    lookup_simulator_by_address = None


class InfiniBox(APITarget):
    OBJECT_TYPES = [Volume, Pool, Host, HostCluster, User, EmailRule, Filesystem, Export, NetworkSpace, NetworkInterface]
    SYSTEM_EVENTS_TYPE = Events
    SYSTEM_COMPONENTS_TYPE = InfiniBoxSystemComponents

    def check_version(self):
        version = self.get_version()
        if not any(version_compatibility.matches(version)
                   for version_compatibility in config.root.infinibox.compatible_versions):
            raise VersionNotSupported(version)

    @property
    @deprecated(message='Use self.host_clusters')
    def clusters(self):
        return self.host_clusters

    def _get_api_auth(self):
        username = self._get_auth_ini_option('username', None)
        password = self._get_auth_ini_option('password', None)
        if not username and not password:
            return None
        elif not username:
            username = 'admin'
        elif not password:
            password = ''

        return username, password

    def _get_auth_ini_option(self, key, default):
        for address in itertools.chain([None], self._addresses):
            if address is None:
                section = 'infinibox'
            else:
                section = 'infinibox:{0}'.format(address[0])
            returned = get_ini_option(section, key, NOTHING)
            if returned is not NOTHING:
                return returned

        return default

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

    def get_luns(self):
        for mapping_obj in itertools.chain(self.host_clusters, self.hosts):
            for lun in mapping_obj.get_luns():
                if lun.is_clustered() and not isinstance(mapping_obj, self.host_clusters.object_type):
                    continue
                yield lun

    luns = property(get_luns)

    def get_state(self):
        return self.components.system_component.get_state()

    def is_simulator(self):
        return "simulator" in self.get_name()

    def get_simulator(self):
        if lookup_simulator_by_address is None:
            return None
        for url in self.api.urls:
            returned = lookup_simulator_by_address(url.hostname)
            if returned is not None:
                return returned
        return None

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

    def get_model_name(self):
        """
        Retrieves the model name as reported by the system
        """
        return self.api.get('config/mgmt/system.model_long_name').get_result()

    def get_version(self):
        """
        Returns the product version of the system
        """
        return self.get_system_info('version')

    def login(self):
        """
        Verifies the current user against the system
        """
        username, password = self.api.get_auth()
        return self.api.post("users/login", data={"username": username, "password": password})
