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
from ..core.type_binder import TypeBinder
from ..core import Field, CapacityType, MillisecondsDatetimeType
from storage_interfaces.scsi.abstracts import ScsiVolume
from ..core.exceptions import InfiniSDKException
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from ..core.utils import deprecated
from .base_data_entity import BaseDataEntity
from .lun import LogicalUnit, LogicalUnitContainer
from .scsi_serial import SCSISerial


class VolumesBinder(TypeBinder):

    def create_many(self, *args, **kwargs):
        """
        Creates multiple volumes with a single call. Parameters are just like ``volumes.create``, only with the
        addition of the ``count`` parameter

        :param count: number of volumes to create. Defaults to 1.
        :rtype: list of volumes
        """
        name = kwargs.pop('name', None)
        if name is None:
            name = Autogenerate('vol_{uuid}').generate()
        count = kwargs.pop('count', 1)
        return [self.create(*args, name='{0}_{1}'.format(name, i), **kwargs)
                for i in range(1, count + 1)]


class Volume(BaseDataEntity):

    BINDER_CLASS = VolumesBinder

    FIELDS = [
        Field("id", type=int, is_identity=True,
              is_filterable=True, is_sortable=True),
        Field(
            "name", creation_parameter=True, mutable=True, is_filterable=True,
            is_sortable=True, default=Autogenerate("vol_{uuid}")),
        Field("size", creation_parameter=True, mutable=True,
              is_filterable=True, is_sortable=True, default=GB, type=CapacityType),
        Field("allocated", type=CapacityType, is_sortable=True, is_filterable=True),
        Field("pool", type='infinisdk.infinibox.pool:Pool', api_name="pool_id", creation_parameter=True, is_filterable=True, is_sortable=True,
              binding=RelatedObjectBinding()),

        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("parent", type='infinisdk.infinibox.volume:Volume', cached=True, api_name="parent_id", binding=RelatedObjectBinding('volumes'), is_filterable=True),
        Field(
            "provisioning", api_name="provtype", mutable=True, creation_parameter=True,
            is_filterable=True, is_sortable=True, default="THICK"),
        Field("created_at", type=MillisecondsDatetimeType),
        Field("serial", type=SCSISerial),
        Field("write_protected", type=bool, mutable=True),
    ]

    @deprecated(message="Use volume.is_master instead")
    def is_master_volume(self):
        return self.is_master()

    def own_replication_snapshot(self, name=None):
        if not name:
            name = Autogenerate('vol_{uuid}')
        data = {'name': name}
        child = self._create(self.system, self.get_this_url_path().add_path('own_snapshot'), data=data)
        return child

    def _get_luns_data_from_url(self):
        res = self.system.api.get(self.get_this_url_path().add_path('luns'))
        return res.get_result()

    def get_lun(self, mapping_object):
        def is_mapping_object_lu(lu_data):
            lu_mapping_id = lu_data['host_cluster_id'] if lu_data[
                'clustered'] else lu_data['host_id']
            return lu_mapping_id == mapping_object.id
        lus = [LogicalUnit(system=self.system, **lu_data)
               for lu_data in self._get_luns_data_from_url() if is_mapping_object_lu(lu_data)]
        if len(lus) > 1:
            raise InfiniSDKException(
                "There shouldn't be multiple luns for volume-mapping object pair")
        return lus[0] if lus else None

    def get_logical_units(self):
        return LogicalUnitContainer.from_dict_list(self.system, self._get_luns_data_from_url())

    def is_mapped(self):
        return self.get_field("mapped")

    def unmap(self):
        """Unmaps a volume from its hosts
        """
        for lun in self.get_logical_units().luns.values():
            lun.unmap()

    def has_children(self):
        return self.get_field("has_children")

ScsiVolume.register(Volume)
