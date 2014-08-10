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

class IPDomain(InfiniBoxObject):
    URL_PATH = 'net/ipds'

    FIELDS = [
        Field("id", is_identity=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("ipdomain_{uuid}")),
        Field("network_config", creation_parameter=True, mutable=True, type=dict, default=dict),
        Field("port_groups", creation_parameter=True, optional=True, mutable=True, type=list, add_updater=False),
        Field("services", creation_parameter=True, optional=True, type=list),
        Field("ips", creation_parameter=False, mutable=False, type=list),
        Field("automatic_ip_failback", creation_parameter=True, mutable=True, optional=True, type=bool),
    ]

    def add_ip_address(self, ip_address):
        return self.system.api.post(self.get_this_url_path().add_path("ips"), data=ip_address).get_result()

    def remove_ip_address(self, ip_address):
        url = self.get_this_url_path().add_path("ips/{0}".format(ip_address))
        return self.system.api.delete(url).get_result()

    def add_port_group(self, port_group):
        return self.system.api.post(self.get_this_url_path().add_path("ports"), data=port_group.id).get_result()

    def remove_port_group(self, port_group):
        url = self.get_this_url_path().add_path("ports").add_path(port_group.id)
        return self.system.api.delete(url).get_result()
