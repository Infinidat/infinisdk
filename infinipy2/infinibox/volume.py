from capacity import GB
from collections import namedtuple
from ..core import Field, SystemObject, CapacityType
from ..core.exceptions import InvalidOperationException
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject

PROVISIONING = namedtuple('Provisioning', ['Thick', 'Thin'])('THICK', 'THIN')
VOLUME_TYPES = namedtuple('VolumeTypes', ['Master', 'Snapshot', 'Clone'])('MASTER', 'SNAP', 'CLONE')


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
        if not name:
            name = Autogenerate('vol_{uuid}')
        data = {'name': name, 'parent_id': self.get_id()}
        resp = self.system.api.post(self.get_url_path(self.system), data=data)
        return self.__class__(self.system, resp.get_result())

    def create_clone(self, name=None):
        if self.is_snapshot():
            return self._create_child(name)
        raise InvalidOperationException('Cannot create clone for volume/clone')

    def create_snapshot(self, name=None):
        if self.is_snapshot():
            raise InvalidOperationException('Cannot create snapshot for snapshot')
        return self._create_child(name)

    def resore(self, snapshot):
        raise NotImplementedError()

    def get_snapshots(self):
        return self.get_children()

    def get_clones(self):
        return self.get_children()

    def get_children(self):
        return self.find(self.system, parent_id=self.get_id())

    def get_parent(self):
        parent_id = self.get_parent_id()
        if parent_id:
            return self.system.volumes.get_by_id_lazy(parent_id)
        return None
