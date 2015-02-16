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
from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.translators_and_types import MunchListType
from .system_object import InfiniBoxObject
from ..core.bindings import RelatedObjectBinding


class Export(InfiniBoxObject):
    FIELDS = [
        Field("id", is_identity=True, type=int),
        Field("export_path", creation_parameter=True, default=Autogenerate("/{prefix}export_{uuid}")),
        Field("inner_path", creation_parameter=True, optional=True),
        Field("filesystem", api_name = "filesystem_id", creation_parameter = True, cached=True, type=int, binding=RelatedObjectBinding()),
        Field("enabled", type=bool, mutable=True),
        Field("make_all_users_anonymous", creation_parameter=True, optional=True),
        Field("anonymous_gid", type=int, creation_parameter=True, optional=True),
        Field("anonymous_uid", type=int, creation_parameter=True, optional=True),
        Field("privileged_port", type=bool, creation_parameter=True, optional=True),
        Field("transport_protocols", creation_parameter=True, optional=True),
        Field("pref_readdir", creation_parameter=True, optional=True, type=CapacityType),
        Field("pref_read", creation_parameter=True, optional=True, type=CapacityType),
        Field("pref_write", creation_parameter=True, optional=True, type=CapacityType),
        Field("max_read", creation_parameter=True, optional=True, type=CapacityType),
        Field("max_write", creation_parameter=True, optional=True, type=CapacityType),
        Field("permissions", type=MunchListType, creation_parameter=True, optional=True),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_nas()
