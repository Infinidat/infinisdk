import logbook
from storage_interfaces.scsi.abstracts import ScsiVolume
from ..core import Field
from ..core.exceptions import InfiniSDKException
from ..core.api.special_values import Autogenerate, OMIT
from ..core.bindings import RelatedObjectBinding
from ..core.object_query import LazyQuery
from ..core.utils import end_reraise_context
from .dataset import Dataset, DatasetTypeBinder
from .lun import LogicalUnit, LogicalUnitContainer
from .scsi_serial import SCSISerial
from .system_object import InfiniBoxObject

_logger = logbook.Logger(__name__)


class VolumesBinder(DatasetTypeBinder):
    def create_group_snapshot(self, volumes, snap_prefix=Autogenerate('{short_uuid}_'), snap_suffix=OMIT):
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
        except Exception as e:  # pylint: disable=broad-except, unused-variable
            with end_reraise_context():
                for v in volumes:
                    v.trigger_cancel_fork()
        else:
            snaps_by_parent_id = {}
            for entity in resp.get_result():
                snaps_by_parent_id[entity['parent_id']] = self.object_type(self.system, entity)
            for v in volumes:
                snap = snaps_by_parent_id.get(v.id)
                if snap is None:
                    _logger.warning('No snapshot was created for {} in group snapshot operation', v)
                    v.trigger_cancel_fork()
                else:
                    v.trigger_finish_fork(snap)
                returned.append(snap)

        return returned



class Volume(Dataset):

    BINDER_CLASS = VolumesBinder

    FIELDS = [
        Field("name", creation_parameter=True, mutable=True, is_filterable=True,
              is_sortable=True, default=Autogenerate("vol_{uuid}")),
        Field("serial", type=SCSISerial, is_filterable=True, is_sortable=True),
        Field("udid", type=int, creation_parameter=True, optional=True, mutable=True, is_filterable=True,
              feature_name='openvms'),
        Field("cons_group", type='infinisdk.infinibox.cons_group:ConsGroup', api_name="cg_id",
              is_filterable=True, is_sortable=True, binding=RelatedObjectBinding('cons_groups', None)),
        Field("parent", type='infinisdk.infinibox.volume:Volume', cached=True, api_name="parent_id",
              binding=RelatedObjectBinding('volumes'), is_filterable=True),
        Field('data_snapshot_guid', is_filterable=True, is_sortable=True, feature_name="nas_replication"),
        Field('paths_available', type=bool, new_to="5.0"),
    ]

    @classmethod
    def create(cls, system, **fields):
        pool = fields.get('pool')
        if pool and isinstance(pool, InfiniBoxObject):
            pool.invalidate_cache('allocated_physical_capacity', 'free_physical_capacity', 'free_virtual_capacity',
                                  'reserved_capacity')
        return super(Volume, cls).create(system, **fields)

    def own_replication_snapshot(self, name=None):
        if not name:
            name = Autogenerate('vol_{uuid}')
        data = {'name': name}
        child = self._create(self.system, self.get_this_url_path().add_path('own_snapshot'), data=data)
        return child

    def reset_serial(self):
        return self.system.api.post(self.get_this_url_path().add_path('reset_serial'))

    def _get_luns_data_from_url(self):
        return LazyQuery(self.system, self.get_this_url_path().add_path('luns')).to_list()

    def get_lun(self, mapping_object):
        """Given either a host or a host cluster object, returns the single LUN object mapped to this volume.

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

    def unmap(self):
        """Unmaps a volume from its hosts
        """
        for lun in self.get_logical_units():
            lun.unmap()
        self.invalidate_cache('mapped')

    def has_children(self):
        return self.get_field("has_children")

    def is_in_cons_group(self):
        return self.get_cons_group() is not None

ScsiVolume.register(Volume)  # pylint: disable=no-member
