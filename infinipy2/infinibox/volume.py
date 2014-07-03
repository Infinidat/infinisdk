import gossip
from capacity import GB
from collections import namedtuple
from ..core import Field, CapacityType, MillisecondsDatetimeType
from storage_interfaces.scsi.abstracts import ScsiVolume
from ..core.exceptions import InvalidOperationException, InfinipyException
from ..core.api.special_values import Autogenerate
from ..core.bindings import RelatedObjectBinding
from .system_object import InfiniBoxObject
from .lun import LogicalUnit, LogicalUnitContainer

PROVISIONING = namedtuple('Provisioning', ['Thick', 'Thin'])('THICK', 'THIN')
VOLUME_TYPES = namedtuple('VolumeTypes', ['Master', 'Snapshot', 'Clone'])('MASTER', 'SNAP', 'CLONE')
_BEGIN_FORK_HOOK = "infinidat.io.begin_fork"
_CANCEL_FORK_HOOK = "infinidat.io.cancel_fork"
_FINISH_FORK_HOOK = "infinidat.io.finish_fork"


def _install_gossip_hooks():
    for hook_name in [_BEGIN_FORK_HOOK, _CANCEL_FORK_HOOK, _FINISH_FORK_HOOK]:
        gossip.define(hook_name)
_install_gossip_hooks()


class Volume(InfiniBoxObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("vol_{uuid}")),
        Field("size", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=GB, type=CapacityType),
        Field("pool", type='infinipy2.infinibox.pool:Pool', api_name="pool_id", creation_parameter=True, is_filterable=True, is_sortable=True, binding=RelatedObjectBinding()),
        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("parent", type='infinipy2.infinibox.volume:Volume', cached=True, api_name="parent_id", binding=RelatedObjectBinding('volumes'), is_filterable=True),
        Field("provisioning", api_name="provtype", mutable=True, creation_parameter=True, is_filterable=True, is_sortable=True, default="THICK"),
        Field("created_at", type=MillisecondsDatetimeType),
    ]

    def get_unique_key(self):
        system_id = self.system.get_api_addresses()[0][0]
        return (system_id, self.get_name())

    def is_master_volume(self):
        return self.get_type() == VOLUME_TYPES.Master

    def is_snapshot(self):
        return self.get_type() == VOLUME_TYPES.Snapshot

    def is_clone(self):
        return self.get_type() == VOLUME_TYPES.Clone

    def _create_child(self, name):
        gossip.trigger(_BEGIN_FORK_HOOK, vol=self)
        if not name:
            name = Autogenerate('vol_{uuid}')
        data = {'name': name, 'parent_id': self.get_id()}
        gossip.trigger('infinidat.pre_object_creation', data=data, system=self.system, cls=type(self))
        try:
            resp = self.system.api.post(self.get_url_path(self.system), data=data)
        except Exception:
            gossip.trigger('infinidat.object_operation_failure')
            gossip.trigger(_CANCEL_FORK_HOOK, vol=self)
            raise
        child = self.__class__(self.system, resp.get_result())
        gossip.trigger('infinidat.post_object_creation', obj=child, data=data)
        gossip.trigger(_FINISH_FORK_HOOK, vol=self, child=child)
        return child

    def create_clone(self, name=None):
        if self.is_snapshot():
            return self._create_child(name)
        raise InvalidOperationException('Cannot create clone for volume/clone')

    def create_snapshot(self, name=None):
        if self.is_snapshot():
            raise InvalidOperationException('Cannot create snapshot for snapshot')
        return self._create_child(name)

    def restore(self, snapshot):
        snapshot_data = int(snapshot.get_field('data'))
        restore_url = self.get_this_url_path().add_path('restore')
        self.system.api.post(restore_url, data=snapshot_data, raw_data=True)

    def own_replication_snapshot(self, name=None):
        if not name:
            name = Autogenerate('vol_{uuid}')
        data = {'name': name}
        gossip.trigger('infinidat.pre_object_creation', data=data, system=self.system, cls=type(self))
        try:
            resp = self.system.api.post(self.get_this_url_path().add_path('own_snapshot'), data=data)
        except Exception:
            gossip.trigger('infinidat.object_operation_failure')
            raise
        child = self.__class__(self.system, resp.get_result())
        gossip.trigger('infinidat.post_object_creation', obj=child, data=data)
        return child

    def get_creation_time(self):
        return self.get_field("created_at", from_cache=True)

    def get_snapshots(self):
        return self.get_children()

    def get_clones(self):
        return self.get_children()

    def _get_luns_data_from_url(self):
        res = self.system.api.get(self.get_this_url_path().add_path('luns'))
        return res.get_result()

    def get_lun(self, mapping_object):
        def is_mapping_object_lu(lu_data):
            lu_mapping_id = lu_data['host_cluster_id'] if lu_data['clustered'] else lu_data['host_id']
            return lu_mapping_id  == mapping_object.id
        lus = [LogicalUnit(system=self.system, **lu_data) for lu_data in self._get_luns_data_from_url() if is_mapping_object_lu(lu_data)]
        if len(lus) > 1:
            raise InfinipyException("There shouldn't be multiple luns for volume-mapping object pair")
        return lus[0] if lus else None

    def get_logical_units(self):
        return LogicalUnitContainer.from_dict_list(self.system, self._get_luns_data_from_url())

    def is_mapped(self):
        return self.get_field("mapped")

    def get_children(self):
        return self.find(self.system, parent_id=self.get_id())

    def has_children(self):
        return self.get_field("has_children")

    def purge(self):
        if self.is_mapped():
            for lun in self.get_logical_units().luns.values():
                lun.unmap()
        for child in self.get_children():
            child.purge()
        super(Volume, self).purge()

ScsiVolume.register(Volume)
