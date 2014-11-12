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
from ..core import Field
from ..core.translators_and_types import MunchType, MunchListType
from ..core.bindings import ListOfRelatedObjectIDsBinding
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject


class NetworkSpace(InfiniBoxObject):
    URL_PATH = 'network/spaces'

    FIELDS = [
        Field("id", is_identity=True, type=int, cached=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("network_space_{uuid}")),
        Field("network_config", creation_parameter=True, mutable=True, type=MunchType),
        Field("interfaces", creation_parameter=True, mutable=True, type=list, binding=ListOfRelatedObjectIDsBinding('network_interfaces')),
        Field("service", creation_parameter=True, default="NAS_SERVICE"),
        Field("ips", creation_parameter=False, mutable=False, type=MunchListType),
        Field("automatic_ip_failback", creation_parameter=True, mutable=True, optional=True, type=bool),
    ]

    @classmethod
    def get_type_name(cls):
        return 'network_space'

    def add_ip_address(self, ip_address):
        res = self.system.api.post(self.get_this_url_path().add_path("ips"), data=ip_address).get_result()
        self.refresh('ips')
        return res

    def remove_ip_address(self, ip_address):
        url = self.get_this_url_path().add_path("ips/{0}".format(ip_address))
        res = self.system.api.delete(url).get_result()
        self.refresh('ips')
        return res

    def disable_ip_address(self, ip_address):
        self.system.api.post(self.get_this_url_path().add_path('ips').add_path(ip_address).add_path('disable'))
        self.refresh('ips')

    def enable_ip_address(self, ip_address):
        self.system.api.post(self.get_this_url_path().add_path('ips').add_path(ip_address).add_path('enable'))
        self.refresh('ips')
