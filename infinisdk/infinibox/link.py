###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from ..core.api.special_values import Autogenerate
from ..core import Field
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import InfiniSDKException
from .system_object import InfiniBoxObject


class Link(InfiniBoxObject):

    FIELDS = [

        Field('id', type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field('name', creation_parameter=True, mutable=True, default=Autogenerate("link_{uuid}")),
        Field('local_replication_network_space', api_name='local_replication_network_space_id',
              binding=RelatedObjectBinding('network_spaces'),
              type='infinisdk.infinibox.network_space:NetworkSpace', creation_parameter=True),
        Field('remote_link_id', type=int),
        Field('remote_host', type=str, creation_parameter=True),
        Field('link_state', type=str),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_replication()

    def delete(self, force_if_remote_error=False):
        """Deletes this link

        :param force_if_remote_error: forces deletion even if remote side caused an API error
        """
        url = self.get_this_url_path()
        if force_if_remote_error:
            url = url.add_query_param('force_if_remote_error', 'true')
        with self._get_delete_context():
            self.system.api.delete(url)

    def get_linked_system(self):
        """Get the corresponsing system object at the remote and of the link. For this to work, the SDK user should
        call the register_related_system method of the Infinibox object when a link to a remote system is consructed
        for the first time"""
        remote_host = self.get_remote_host()
        for related_system in self.get_system().iter_related_systems():
            for network_space in related_system.network_spaces.get_all():
                for ip in network_space.get_ips():
                    if ip.ip_address == remote_host:
                        return related_system

        raise InfiniSDKException("Could not find a related machine with IP address {0}".format(remote_host))
