import gossip
from capacity import Capacity, byte
from urlobject import URLObject as URL
from collections import namedtuple
from ..core.api.special_values import Autogenerate
from ..core.utils import deprecated
from ..core.exceptions import InvalidOperationException
from ..core.type_binder import TypeBinder, PolymorphicBinder
from .system_object import InfiniBoxObject

_BEGIN_FORK_HOOK = "infinidat.sdk.begin_fork"
_CANCEL_FORK_HOOK = "infinidat.sdk.cancel_fork"
_FINISH_FORK_HOOK = "infinidat.sdk.finish_fork"


class Datasets(PolymorphicBinder):

    def __init__(self, system):
        object_types = (system.volumes.object_type, system.filesystems.object_type)
        super(Datasets, self).__init__(URL('datasets'), object_types, factory=self._dataset_factory, system=system)

    def is_supported(self):
        return self.system.filesystems.is_supported()

    def _dataset_factory(self, system, received_item):
        dataset_type_str = received_item['dataset_type']
        assert dataset_type_str in ('VOLUME', 'FILESYSTEM'), 'Unsupported dataset type {}'.format(dataset_type_str)
        dataset_binder = system.objects.get_binder_by_type_name(dataset_type_str.lower())
        return dataset_binder.object_type.construct(system, received_item)


class DatasetTypeBinder(TypeBinder):
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

    def calculate_reclaimable_space(self, entities):
        return self.system.api.post(URL(self.object_type.get_url_path(self.system)).add_path('delete_simulation'), data=dict(entities=[entity.id for entity in entities])).get_result()['space_reclaimable'] * byte


class Dataset(InfiniBoxObject):
    PROVISIONING = namedtuple('Provisioning', ['Thick', 'Thin'])('THICK', 'THIN')


    def _get_snapshot_type(self):
        return 'SNAPSHOT' if self.system.compat.has_writable_snapshots() else 'SNAP'

    def get_family_master(self):
        if self.is_master():
            return self
        return self.get_binder().get_by_id_lazy(self.get_family_id())

    def is_master(self):
        """Returns whether or not this entity is a master entity (not a snapshot and not a clone)
        """
        return self.get_type() == 'MASTER'

    def refresh_snapshot(self):
        """Refresh a snapshot with the most recent data from the parent
        """
        parent = self.get_parent()
        parent.trigger_begin_fork()
        try:
            self.system.api.post(self.get_this_url_path().add_path('refresh'), data={'source_id': parent.id})
        except Exception:
            parent.trigger_cancel_fork()
            raise
        parent.trigger_finish_fork(self)

    def is_snapshot(self):
        """Returns whether or not this entity is a snapshot
        """
        return self.get_type() == self._get_snapshot_type()

    @deprecated
    def is_clone(self):
        """Returns whether or not this entity is a clone
        """
        assert not self.system.compat.has_writable_snapshots(), '{}.is_clone() with snapclones is not supported'.format(
            self.__class__.__name__)
        return self.get_type() == 'CLONE'

    def resize(self, delta):
        """Resize the entity by the given delta"""
        assert isinstance(delta, Capacity), "Delta must be an instance of Capacity"
        return self.update_field('size', self.get_size() + delta)

    def create_child(self, name=None):
        self.invalidate_cache('has_children')
        self.trigger_begin_fork()
        if not name:
            name = self.fields.name.generate_default().generate()
        data = {'name': name, 'parent_id': self.get_id()}
        try:
            child = self._create(self.system, self.get_url_path(self.system), data=data, tags=self._get_tags_for_object_operations(self.system))
        except Exception:
            self.trigger_cancel_fork()
            raise
        self.trigger_finish_fork(child)
        self._handle_possible_replication_snapshot(child)
        return child

    def trigger_begin_fork(self):
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags(_BEGIN_FORK_HOOK, {'obj': self}, tags=hook_tags)

    def trigger_cancel_fork(self):
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags(_CANCEL_FORK_HOOK, {'obj': self}, tags=hook_tags)

    def trigger_finish_fork(self, child):
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags(_FINISH_FORK_HOOK, {'obj': self, 'child': child}, tags=hook_tags)

    def _handle_possible_replication_snapshot(self, snapshot):
        fields = snapshot.get_fields(from_cache=True, raw_value=True)
        if fields.get('rmr_snapshot_guid', None) is not None:
            gossip.trigger_with_tags('infinidat.sdk.replica_snapshot_created', {'snapshot': snapshot}, tags=['infinibox'])

    @deprecated
    def create_clone(self, name=None):
        """Creates a clone from this entity, if supported by the system
        """
        assert not self.system.compat.has_writable_snapshots(), '{}.create_clone() with snapclones is not supported'.format(
            self.__class__.__name__)
        if self.is_snapshot():
            return self.create_child(name)
        raise InvalidOperationException('Cannot create clone for volume/clone')

    def create_snapshot(self, name=None):
        """Creates a snapshot from this entity, if supported by the system
        """
        if not self.system.compat.has_writable_snapshots() and self.is_snapshot():
            raise InvalidOperationException('Cannot create snapshot for snapshot')
        return self.create_child(name)

    def restore(self, snapshot):
        """Restores this entity from a given snapshot object
        """
        snapshot_id = snapshot.id
        restore_url = self.get_this_url_path().add_path('restore')
        self.trigger_before_restore(snapshot)
        try:
            self.system.api.post(restore_url, data=snapshot_id)
        except Exception as e:
            self.trigger_data_restore_failure(snapshot, e)
            raise
        self.trigger_after_restore(snapshot)

    def trigger_before_restore(self, source):
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.pre_data_restore', {'source': source, 'target': self}, tags=hook_tags)

    def trigger_data_restore_failure(self, source, e):
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.data_restore_failure', {'source': source, 'target': self, 'exc': e}, tags=hook_tags)

    def trigger_after_restore(self, source):
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.post_data_restore', {'source': source, 'target': self}, tags=hook_tags)

    def get_snapshots(self):
        """Retrieves all snapshot children of this entity
        """
        return self.get_children(type=self._get_snapshot_type())

    @deprecated
    def get_clones(self):
        """Retrieves all clone children of this entity
        """
        assert not self.system.compat.has_writable_snapshots(), '{}.get_clones() with snapclones is not supported'.format(
            self.__class__.__name__)
        return self.get_children(type='CLONE')

    def get_children(self, **kwargs):
        """Retrieves all child entities for this entity (either clones or snapshots)
        """
        return self.find(self.system, parent_id=self.get_id(), **kwargs)

    def has_children(self):
        """Returns whether or not this entity has children
        """
        return len(self.get_children()) > 0

    def get_creation_time(self):
        """Retrieves creation time for this entity
        """
        return self.get_field("created_at", from_cache=True)

    def calculate_reclaimable_space(self):
        return self.system.api.post(URL(self.get_url_path(self.system)).add_path('delete_simulation'), data=dict(entities=[self.id])).get_result()['space_reclaimable'] * byte

    @InfiniBoxObject.requires_cache_invalidation("pool")
    def move_pool(self, target_pool, with_capacity=False):
        """Moves this entity to a new pool, optionally along with its needed capacity
        """
        data = dict(pool_id=target_pool.get_id(), with_capacity=with_capacity)
        self.system.api.post(self.get_this_url_path().add_path('move'), data=data)
