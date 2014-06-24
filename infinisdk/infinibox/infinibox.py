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

from ..core.api import APITarget
from ..core.config import config
from .cluster import Cluster
from .components import InfiniBoxSystemComponents
from .events import EmailRule, Events
from .host import Host
from .lun import LogicalUnit
from .pool import Pool
from .user import User
from .volume import Volume


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

    def get_luns(self):
        for mapping_obj in itertools.chain(self.clusters, self.hosts):
            for lun in mapping_obj.get_luns():
                if lun.is_clustered() and not isinstance(mapping_obj, self.clusters.object_type):
                    continue
                yield lun

    luns = property(get_luns)

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

    def login(self):
        """
        Verifies the current user against the system
        """
        username, password = self.api.get_auth()
        return self.api.post("users/login", data={"username": username, "password": password})
