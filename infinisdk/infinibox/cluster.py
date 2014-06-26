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
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxLURelatedObject


class Cluster(InfiniBoxLURelatedObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("cluster_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("hosts", api_name="hosts", type=list, add_getter=False, add_updater=False),
    ]

    def add_host(self, host):
        url = "{0}/hosts".format(self.get_this_url_path())
        self.system.api.post(url, data={"id" : host.id})

    def remove_host(self, host):
        url = "{0}/hosts/{1}".format(self.get_this_url_path(), host.id)
        self.system.api.delete(url)

    def get_hosts(self):
        return [self.system.hosts.get_by_id_lazy(host_attrs['id'])
                for host_attrs in self.get_field('hosts')]
