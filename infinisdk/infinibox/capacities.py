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

from infi.pyutils.lazy import cached_method
from urlobject import URLObject as URL
from ..core.system_object import SystemObject
from ..core.field import Field
from ..core.translators_and_types import CapacityType
from api_object_schema.binding import ConstBinding


class InfiniBoxSystemCapacity(SystemObject):
    URL_PATH = URL("/api/rest/system/capacity")
    FIELDS = [
        Field("id", binding=ConstBinding('capacity'), is_identity=True, cached=True),
        Field("free_physical_capacity", api_name="free_physical_space", type=CapacityType),
        Field("free_virtual_capacity", api_name="free_virtual_space", type=CapacityType),
        Field("total_physical_capacity", type=CapacityType),
        Field("total_virtual_capacity", type=CapacityType)
    ]

    def __init__(self, system):
        super(InfiniBoxSystemCapacity, self).__init__(system, {})

    @cached_method
    def get_this_url_path(self):
        return self.URL_PATH
