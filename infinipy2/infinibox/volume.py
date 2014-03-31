from capacity import GB
from collections import namedtuple
from ..core import Field, SystemObject, CapacityType
from storage_interfaces.scsi.abstracts import ScsiVolume
from ..core.exceptions import InvalidOperationException, InfinipyException
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject
from .lun import LogicalUnit
import slash

PROVISIONING = namedtuple('Provisioning', ['Thick', 'Thin'])('THICK', 'THIN')
VOLUME_TYPES = namedtuple('VolumeTypes', ['Master', 'Snapshot', 'Clone'])('MASTER', 'SNAP', 'CLONE')


def _install_slash_fork_hooks():
    for phase in ["begin", "cancel", "finish"]:
        slash.hooks.ensure_custom_hook("{0}_fork".format(phase))
_install_slash_fork_hooks()


class Volume(InfiniBoxObject):

    FIELDS = [
        Field("id", is_identity=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("vol_{uuid}")),
        Field("size", creation_parameter=True, mutable=True, default=GB, type=CapacityType),
        Field("pool_id", creation_parameter=True),
        Field("type", cached=True),
        Field("parent_id", cached=True),
        Field("provisioning", api_name="provtype", mutable=True, creation_parameter=True, default="THICK"),
    ]

    def get_pool(self):
        return self.system.pools.get_by_id_lazy(self.get_pool_id())

    def get_unique_key(self):
        system_id = self.system.get_api_addresses()[0][0]
        return (system_id, self.get_name())

    @classmethod
    def create(cls, system, **fields):
        pool = fields.pop('pool', None)
        if isinstance(pool, SystemObject):
            fields['pool_id'] = pool.id
        return super(Volume, cls).create(system, **fields)

    def is_master_volume(self):
        return self.get_type() == VOLUME_TYPES.Master

    def is_snapshot(self):
        return self.get_type() == VOLUME_TYPES.Snapshot

    def is_clone(self):
        return self.get_type() == VOLUME_TYPES.Clone

    def _create_child(self, name):
        slash.hooks.begin_fork(vol=self)
        if not name:
            name = Autogenerate('vol_{uuid}')
        data = {'name': name, 'parent_id': self.get_id()}
        slash.hooks.pre_object_creation(data=data, system=self.system, cls=type(self))
        try:
            resp = self.system.api.post(self.get_url_path(self.system), data=data)
        except Exception:
            slash.hooks.object_operation_failure()
            slash.hooks.cancel_fork(vol=self)
            raise
        child = self.__class__(self.system, resp.get_result())
        slash.hooks.post_object_creation(obj=child, data=data)
        slash.hooks.finish_fork(vol=self, child=child)
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
        self.update_field('data', snapshot_data)

    def get_snapshots(self):
        return self.get_children()

    def get_clones(self):
        return self.get_children()

    def _get_lun(self):
        res = self.system.api.get(self.get_this_url_path().add_path('luns'))
        return res.get_result()

    def get_lun(self):
        luns_data = self._get_lun()
        if len(luns_data) > 1:
            raise InfinipyException('Volume could not have multiple luns')
        return LogicalUnit(self.system, **luns_data[0])

    def is_mapped(self):
        luns_data = self._get_lun()
        return len(luns_data) != 0

    def get_children(self):
        return self.find(self.system, parent_id=self.get_id())

    def has_children(self):
        return len(self.get_children()) != 0

    def get_parent(self):
        parent_id = self.get_parent_id()
        if parent_id:
            return self.system.volumes.get_by_id_lazy(parent_id)
        return None

ScsiVolume.register(Volume)
