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

class Export(InfiniBoxObject):
    FIELDS = [
        Field("id", is_identity=True, type=int),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("export_{uuid}")),
        Field("export_path", creation_parameter=True, mutable=True, default=Autogenerate("/export_{uuid}")),
        Field("inner_path", creation_parameter=True, mutable=True, default='/'),
        Field("filesystem_id", cached=True, type=int),
    ]

    @classmethod
    def create(cls, system, **fields):
        filesystem = fields.pop('filesystem', None)
        if isinstance(filesystem, SystemObject):
            fields['filesystem_id'] = filesystem.id  # workaound (filesystem_id mismatch)
        return super(Export, cls).create(system, **fields)