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
from ..core.bindings import RelatedObjectBinding
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxLURelatedObject
from infi.dtypes.wwn import WWN


class Host(InfiniBoxLURelatedObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("host_{uuid}")),
        Field("luns", type=list, add_getter=False, add_updater=False),
        Field("ports", type=list, add_getter=False, add_updater=False),
        Field("cluster", api_name="host_cluster_id", type='infinisdk.infinibox.cluster:Cluster', is_filterable=True, binding=RelatedObjectBinding()),
    ]

    def _add_port(self, port_type, port_address):
        port_wwn = str(WWN(port_address))
        data = dict(address=port_wwn, type=port_type)
        url = "{0}/ports".format(self.get_this_url_path())
        self.system.api.post(url, data=data)
        self.refresh('ports')

    def add_fc_port(self, port_address):
        """
        Adds an FC port address (WWN) to this host
        :param port_address: A string representing the WWN to add (e.g. ``00:11:22:33:44:55:66``)
        """
        return self._add_port('fc', port_address)

    def remove_fc_port(self, port_address):
        """
        Removes a FC port address (WWN) to this host
        """
        return self._remove_port('fc', port_address)

    def _remove_port(self, port_type, port_address):
        port_wwn = str(WWN(port_address))
        url = "{0}/ports/{1}/{2}".format(self.get_this_url_path(),
                                         port_type, port_wwn)
        self.system.api.delete(url)
        self.refresh('ports')

    def get_fc_ports(self):
        """
        Returns all FC ports defined on this host
        """
        return self._get_ports('fc')

    def _get_ports(self, port_type):
        lowered_port_type = port_type.lower()
        return [WWN(port['address'])
                for port in self.get_field('ports')
                    if port['type'].lower() == lowered_port_type]
