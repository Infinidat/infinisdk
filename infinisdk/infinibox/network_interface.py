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
from ..core import Field
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject
from ..core.bindings import ListToDictBinding, RelatedComponentBinding


class NetworkInterface(InfiniBoxObject):
    URL_PATH = 'network/interfaces'

    FIELDS = [
        Field("id", is_identity=True, type=int, cached=True),
        Field("ports", optional=True, creation_parameter=True, mutable=True, type=list, default=list, add_updater=False, binding=ListToDictBinding(key="name")),
        Field("node", api_name="node_id", creation_parameter=True, mutable=False, type=int, binding=RelatedComponentBinding()),
        Field("state", cached=False),
        Field("type", creation_parameter=True, default="PORT_GROUP"),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("pg_{uuid}")), # should contain the node id somehow
    ]

    @classmethod
    def get_type_name(cls):
        return 'network_interface'

    def add_port(self, port):
        url = self.get_this_url_path().add_path("ports")
        data = self.fields.ports.binding.get_api_value_from_value(None, None, None, [port])[0]
        return self.system.api.post(url, data=data).get_result()

    def remove_port(self, port):
        url = self.get_this_url_path().add_path("ports").add_path("{0}".format(port))
        return self.system.api.delete(url).get_result()

    def disable(self):
        url = self.get_this_url_path().add_path("disable")
        return self.system.api.post(url)

    def enable(self):
        url = self.get_this_url_path().add_path("enable")
        return self.system.api.post(url)

    def is_enabled(self):
        # FIXME: Need to be changed after INFINIBOX-12968 will be resolved
        return self.get_state() == 'OK'

    def __repr__(self):
        return "<{0} id={1} node={2}>".format(type(self).__name__, self.id, self.get_field("node"))
