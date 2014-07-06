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
from ..core.api import APITarget
from ..core.config import config
from .components import IZBoxSystemComponents
from .filesystem import Filesystem, Snapshot
from .user import User
from .events import Events, PushRule

class IZBox(APITarget):
    OBJECT_TYPES = [Filesystem, Snapshot, User, PushRule]
    SYSTEM_COMPONENTS_TYPE = IZBoxSystemComponents
    SYSTEM_EVENTS_TYPE = Events

    def _is_simulator(self, address):
        return type(address).__name__ == "Simulator"

    def _get_simulator_address(self, address):
        port = address.base_url.netloc.port or 80
        return (address.base_url.netloc.hostname, port)

    def check_version(self):
        pass # TODO: implement version checking for IZBox

    def get_approval_failure_codes(self):
        d = config.get_path('izbox.approval_required_codes')
        return d

    def get_state(self):
        return self.components.system_component.get_state()

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

    def _get_api_timeout(self):
        return config.get_path('izbox.defaults.system_api.timeout_seconds')

