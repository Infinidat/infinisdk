from capacity import GB
from storage_interfaces.scsi.abstracts import ScsiVolume
from ..core.type_binder import TypeBinder
from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.exceptions import InfiniSDKException, ObjectNotFound, TooManyObjectsFound
from ..core.api.special_values import Autogenerate, SpecialValue, OMIT
from ..core.bindings import RelatedObjectBinding
from ..core.utils import DONT_CARE
from .dataset import Dataset
from .lun import LogicalUnit, LogicalUnitContainer
from .scsi_serial import SCSISerial


class VolumesBinder(TypeBinder):

    def create_many(self, *args, **kwargs):
        """
        Creates multiple volumes with a single call. Parameters are just like ``volumes.create``, only with the
        addition of the ``count`` parameter

        Returns: list of volumes

        :param count: number of volumes to create. Defaults to 1.
        """
        name = kwargs.pop('name', None)
        if name is None:
            name = Autogenerate('vol_{uuid}').generate()
        count = kwargs.pop('count', 1)
        return [self.create(*args, name='{0}_{1}'.format(name, i), **kwargs)
                for i in range(1, count + 1)]

    def create_group_snapshot(self, volumes, snap_prefix=Autogenerate('{ordinal}'), snap_suffix=OMIT):
        """
        Creates multiple snapshots with a single consistent point-in-time, returning the snapshots
        in respective order to parent volumes

        :param volumes: list of volumes we should create a snapshot of
        """
        volumes = list(volumes)
        returned = []
        for v in volumes:
            v.trigger_begin_fork()
        try:
            resp = self.system.api.post('volumes/group_snapshot', data={
                'snap_prefix': snap_prefix,
                'snap_suffix': snap_suffix,
                'entities': [
                    {'id': v.id}
                    for v in volumes
                ]
            })
        except:
            for v in volumes:
                v.trigger_cancel_fork()
            raise
        else:
            snaps_by_parent_id = {}
            for entity in resp.get_result():
                snaps_by_parent_id[entity['parent_id']] = self.object_type(self.system, entity)
            for v in volumes:
                snap = snaps_by_parent_id.get(v.id)
                if snap is None:
                    _logger.warning('No snapshot was created for {0} in group snapshot operation', v)
                    v.trigger_cancel_fork()
                else:
                    v.trigger_finish_fork(snap)
                returned.append(snap)

        return returned



class Volume(Dataset):

    BINDER_CLASS = VolumesBinder

    FIELDS = [
        Field("id", type=int, is_identity=True,
              is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True,
            is_sortable=True, default=Autogenerate("vol_{uuid}")),
        Field("size", creation_parameter=True, mutable=True,
              is_filterable=True, is_sortable=True, default=GB, type=CapacityType),
        Field("used_size", api_name="used", type=CapacityType),
        Field("allocated", type=CapacityType, is_sortable=True, is_filterable=True),
        Field("tree_allocated", type=CapacityType),
        Field("pool", type='infinisdk.infinibox.pool:Pool', api_name="pool_id", creation_parameter=True, is_filterable=True, is_sortable=True,
              binding=RelatedObjectBinding()),
        Field("cons_group", type='infinisdk.infinibox.cons_group:ConsGroup', api_name="cg_id", is_filterable=True, is_sortable=True,
              binding=RelatedObjectBinding('cons_groups', None)),
        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("parent", type='infinisdk.infinibox.volume:Volume', cached=True, api_name="parent_id",
                binding=RelatedObjectBinding('volumes'), is_filterable=True),
        Field("family_id", type=int, cached=True, is_filterable=True, is_sortable=True),
        Field("provisioning", api_name="provtype", mutable=True, creation_parameter=True,
                is_filterable=True, is_sortable=True, default="THICK"),
        Field("created_at", cached=True, type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("serial", type=SCSISerial, is_filterable=True, is_sortable=True),
        Field("ssd_enabled", type=bool, mutable=True, creation_parameter=True, is_filterable=True, is_sortable=True, optional=True, toggle_name='ssd'),
        Field("write_protected", type=bool, mutable=True, creation_parameter=True, optional=True
              , is_filterable=True, is_sortable=True, toggle_name='write_protection'),
        Field("compression_enabled", type=bool, mutable=True, creation_parameter=True, optional=True, feature_name='compression', toggle_name='compression'),
        Field("compression_supressed", type=bool, feature_name='compression'),
        Field("capacity_savings", type=CapacityType, feature_name='compression'),
        Field("depth", cached=True, type=int, is_sortable=True, is_filterable=True),
        Field("mapped", type=bool, is_sortable=True, is_filterable=True),
        Field("has_children", type=bool, add_getter=False),
        Field('rmr_source', type=bool),
        Field('rmr_target', type=bool),
    ]

    @classmethod
    def create(cls, system, **fields):
        pool = fields.get('pool')
        if pool and not isinstance(pool, SpecialValue):
            pool.refresh('allocated_physical_capacity', 'free_physical_capacity', 'free_virtual_capacity', 'reserved_capacity')
        return super(Volume, cls).create(system, **fields)

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
        """Given either a host or a host cluster object, returns the single LU object mapped to this volume.

        An exception is raised if multiple matching LUs are found

        :param mapping_object: Either a host cluster or a host object to be checked
        :returns: None if no lu is found for this entity
        """
        def is_mapping_object_lu(lu_data):
            lu_mapping_id = lu_data['host_id'] or lu_data['host_cluster_id']
            return lu_mapping_id == mapping_object.id
        lus = [LogicalUnit(system=self.system, **lu_data)
               for lu_data in self._get_luns_data_from_url() if is_mapping_object_lu(lu_data)]
        if len(lus) > 1:
            raise InfiniSDKException("There shouldn't be multiple luns for volume-mapping object pair")
        return lus[0] if lus else None

    def get_logical_units(self):
        return LogicalUnitContainer.from_dict_list(self.system, self._get_luns_data_from_url())

    def get_replicas(self):
        pairs = self.system.api.get(self.get_this_url_path().add_path('replication_pairs')).response.json()['result']
        return [self.system.replicas.get_by_id_lazy(pair['replica_id']) for pair in pairs]

    def get_replica(self):
        returned = self.get_replicas()
        if len(returned) > 1:
            raise TooManyObjectsFound('Replicas of {}'.format(self))
        elif len(returned) == 0:
            raise ObjectNotFound('Replicas of {}'.format(self))
        return returned[0]

    def is_replicated(self, from_cache=DONT_CARE):
        """Returns True if this volume is a part of a replica, whether as source or as target
        """
        return any(self.get_fields(['rmr_source', 'rmr_target'], from_cache=from_cache).values())

    def unmap(self):
        """Unmaps a volume from its hosts
        """
        for lun in self.get_logical_units():
            lun.unmap()
        self.refresh('mapped')

    def has_children(self):
        return self.get_field("has_children")

ScsiVolume.register(Volume)
