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
from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject
from ..core.bindings import ListToDictBinding

class PortGroup(InfiniBoxObject):
    URL_PATH = 'network/port_groups'

    FIELDS = [
        Field("id", is_identity=True),
        Field("ports", creation_parameter=True, mutable=True, type=list, default=list, add_updater=False, binding=ListToDictBinding(key="name")),
        Field("node", api_name="node_id", creation_parameter=True, mutable=False, type=int),
        Field("state"),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("pg_{uuid}")), # should contain the node id somehow
    ]

    def add_port(self, port):
        url = self.get_this_url_path().add_path("ports")
        data = self.fields.ports.binding.get_raw_api_value([port])[0]
        return self.system.api.post(url, data=data).get_result()

    def remove_port(self, port):
        url = self.get_this_url_path().add_path("ports").add_path("{0}".format(port))
        return self.system.api.delete(url).get_result()

    def disable(self):
        url = self.get_this_url_path().add_path("disable")
        return self.system.api.post(url, data = "1")

    def enable(self):
        url = self.get_this_url_path().add_path("enable")
        return self.system.api.post(url, data = "1")
