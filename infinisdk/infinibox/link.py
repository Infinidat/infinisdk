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
from .system_object import InfiniBoxObject


class Link(InfiniBoxObject):

    FIELDS = [

        Field('id', type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field('name', creation_parameter=True, mutable=True),
        Field('local_replication_network_space', api_name='local_replication_network_space_id',
              binding=RelatedObjectBinding('network_spaces'),
              type='infinisdk.infinibox.network_space:NetworkSpace', creation_parameter=True),
        Field('remote_link_id', type=int),
        Field('remote_host', type=str, creation_parameter=True),
        Field('link_state', type=str),
    ]

    def delete(self, force_if_remote_error=False):
        """Deletes this link

        :param force_if_remote_error: forces deletion even if remote side caused an API error
        """
        url = self.get_this_url_path()
        if force_if_remote_error:
            url = url.add_query_param('force_if_remote_error', 'true')
        self.system.api.delete(url)
