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
from capacity import GB
from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from .base_data_entity import BaseDataEntity


# TODO: use a common baseclass for volume and filesystem

class Filesystem(BaseDataEntity):

    FIELDS = [
        Field("id", type=int, is_identity=True,
              is_filterable=True, is_sortable=True),
        Field(
            "name", creation_parameter=True, mutable=True, is_filterable=True,
            is_sortable=True, default=Autogenerate("fs_{uuid}")),
        Field("size", creation_parameter=True, mutable=True,
              is_filterable=True, is_sortable=True, default=GB, type=CapacityType),
        Field("pool", type='infinisdk.infinibox.pool:Pool', api_name="pool_id", creation_parameter=True, is_filterable=True, is_sortable=True,
              binding=RelatedObjectBinding()),
        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("parent", type='infinisdk.infinibox.filesystem:Filesystem', cached=True, api_name="parent_id", binding=RelatedObjectBinding('filesystems'), is_filterable=True),
        Field("provisioning", api_name="provtype", mutable=True, creation_parameter=True,
            is_filterable=True, is_sortable=True, default="THICK"),
        Field("created_at", type=MillisecondsDatetimeType),
        Field("write_protected", type=bool, mutable=True, creation_parameter=True, optional=True),
    ]

    def add_export(self, **kwargs):
        return self.system.exports.create(filesystem=self, **kwargs)

    def get_exports(self):
        # TODO: FIXME: INFINIBOX-11698, please revert when fixed
        return [e for e in self.system.exports.get_all() if e.get_filesystem() == self]
        #return self.system.exports.find(self.system.objects.exports.fields.filesystem_id == self.id)

    def move_pool(self, target_pool, with_capacity=True):
        raise NotImplementedError("Not implemented in infinibox 2.0.0.0")
