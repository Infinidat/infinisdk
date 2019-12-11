import functools
import gossip
import logbook
from capacity import Capacity, byte, GB
from urlobject import URLObject as URL
from collections import namedtuple
from mitba import cached_method
from ..core.utils import (
    DONT_CARE,
    add_normalized_query_params,
    end_reraise_context,
    handle_possible_replication_snapshot,
)
from ..core.exceptions import ObjectNotFound, TooManyObjectsFound
from ..core.type_binder import TypeBinder, PolymorphicBinder
from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.bindings import RelatedObjectBinding, RelatedObjectNamedBinding
from ..core.api.special_values import OMIT
from .system_object import InfiniBoxObject

_BEGIN_FORK_HOOK = "infinidat.sdk.begin_fork"
_CANCEL_FORK_HOOK = "infinidat.sdk.cancel_fork"
_FINISH_FORK_HOOK = "infinidat.sdk.finish_fork"

_logger = logbook.Logger(__name__)


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
            name = self.fields.name.generate_default().generate()
        count = kwargs.pop('count', 1)
        return [self.create(*args, name='{}_{}'.format(name, i), **kwargs)
                for i in range(1, count + 1)]

    def calculate_reclaimable_space(self, entities):
        url = URL(self.object_type.get_url_path(self.system)).add_path('delete_simulation')
        res = self.system.api.post(url, data=dict(entities=[entity.id for entity in entities]))
        return res.get_result()['space_reclaimable'] * byte


class Dataset(InfiniBoxObject):

    FIELDS = [
        Field("id", type=int, is_identity=True,
              is_filterable=True, is_sortable=True),
        Field("dataset_type", is_filterable=True, is_sortable=True),
        Field("num_blocks", type=int),
        Field("size", creation_parameter=True, mutable=True,
              is_filterable=True, is_sortable=True, default=GB, type=CapacityType),
        Field("used_size", api_name="used", type=CapacityType),
        Field("allocated", type=CapacityType, is_sortable=True, is_filterable=True),
        Field("tree_allocated", type=CapacityType),
        Field("pool", type='infinisdk.infinibox.pool:Pool', api_name="pool_id", creation_parameter=True,
              is_filterable=True, is_sortable=True, binding=RelatedObjectNamedBinding()),
        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("family_id", type=int, cached=True, is_filterable=True, is_sortable=True, new_to="3.0"),
        Field("provisioning", api_name="provtype", mutable=True, creation_parameter=True,
              is_filterable=True, is_sortable=True, default="THICK"),
        Field("created_at", cached=True, type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("ssd_enabled", type=bool, mutable=True, creation_parameter=True,
              is_filterable=True, is_sortable=True, optional=True, toggle_name='ssd'),
        Field("write_protected", type=bool, mutable=True, creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True, toggle_name='write_protection'),
        Field("compression_enabled", type=bool, mutable=True, creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True, feature_name='compression', toggle_name='compression'),
        Field("compression_suppressed", type=bool, feature_name='compression'),
        Field("capacity_savings", type=CapacityType, feature_name='compression'),
        Field("depth", cached=True, type=int, is_sortable=True, is_filterable=True),
        Field("mapped", type=bool, is_sortable=True, is_filterable=True),
        Field("has_children", type=bool, add_getter=False),
        Field('rmr_source', type=bool, is_sortable=True, is_filterable=True),
        Field('rmr_target', type=bool, is_sortable=True, is_filterable=True),
        Field('rmr_snapshot_guid', is_filterable=True, is_sortable=True),
        Field('qos_policy', type='infinisdk.infinibox.qos_policy:QosPolicy', api_name='qos_policy_id', is_sortable=True,
              is_filterable=True, binding=RelatedObjectBinding('qos_policies'), feature_name='qos', cached=False),
        Field('qos_shared_policy', type='infinisdk.infinibox.qos_policy:QosPolicy', api_name='qos_shared_policy_id',
              is_sortable=True, is_filterable=True, binding=RelatedObjectBinding('qos_policies'),
              feature_name='qos', cached=False),
        Field('pool_name', is_sortable=True, is_filterable=True, new_to="4.0.10"),
        Field("lock_expires_at", type=MillisecondsDatetimeType, mutable=True, creation_parameter=True,
              optional=True, feature_name='snapshot_lock'),
        Field("lock_state", type=str, feature_name='snapshot_lock'),
        Field('rmr_active_active_peer', type=bool, is_sortable=True, is_filterable=True, feature_name='active_active'),
        Field('replica_ids', type=list, new_to="5.0"),
        Field("tenant", api_name="tenant_id", binding=RelatedObjectBinding('tenants'),
              type='infinisdk.infinibox.tenant:Tenant', feature_name='tenants', is_filterable=True, is_sortable=True),
    ]

    PROVISIONING = namedtuple('Provisioning', ['Thick', 'Thin'])('THICK', 'THIN')
    _forked_obj = None

    def _get_snapshot_type(self):
        return 'SNAPSHOT' if self.system.compat.has_writable_snapshots() else 'SNAP'

    @cached_method
    def _get_family_master_id(self):
        assert not self.is_field_supported('family_id'), "Use self.get_family_id(), which adheres to cache policies"
        if self.is_master():
            return self.get_id()
        return self.get_parent()._get_family_master_id()  # pylint: disable=protected-access

    def get_family_master(self):
        if self.is_master():
            return self

        if self.is_field_supported('family_id'):
            family_master_id = self.get_family_id()
        else:
            family_master_id = self._get_family_master_id()
        if family_master_id is None:
            return None
        return self.get_binder().get_by_id_lazy(family_master_id)

    def is_master(self):
        """Returns whether or not this entity is a master entity (not a snapshot and not a clone)
        """
        return self.get_type() == 'MASTER'

    def refresh_snapshot(self, force_if_replicated_on_target=OMIT):
        """Refresh a snapshot with the most recent data from the parent
        :param force_if_replicated_on_target: (Only required on some InfiniBox versions) allows the refresh operation
        to occur on a dataset that is currently a replication target.
        """
        parent = self.get_parent()
        assert parent, "Cannot refresh_snapshot on master volume"
        trigger_hook = functools.partial(gossip.trigger_with_tags,
                                         kwargs={'source': parent, 'target': self},
                                         tags=self.get_tags_for_object_operations(self.system))
        trigger_hook('infinidat.sdk.pre_refresh_snapshot')
        parent.trigger_begin_fork()
        url = add_normalized_query_params(self.get_this_url_path().add_path("refresh"),
                                          force_if_replicated_on_target=force_if_replicated_on_target)
        try:
            self.system.api.post(url, data={'source_id': parent.id})
        except Exception:  # pylint: disable=broad-except
            with end_reraise_context():
                parent.trigger_cancel_fork()
                trigger_hook('infinidat.sdk.refresh_snapshot_failure')
        parent.trigger_finish_fork(self)
        trigger_hook('infinidat.sdk.post_refresh_snapshot')

    def is_snapshot(self):
        """Returns whether or not this entity is a snapshot
        """
        return self.get_type() == self._get_snapshot_type()

    def resize(self, delta):
        """Resize the entity by the given delta"""
        assert isinstance(delta, Capacity), "Delta must be an instance of Capacity"
        return self.update_field('size', self.get_size() + delta)

    def _create_child(self, name=None, **kwargs):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.pre_entity_child_creation',
                                 {'source': self, 'system': self.system},
                                 tags=hook_tags)

        self.invalidate_cache('has_children')
        self.trigger_begin_fork()
        if not name:
            name = self.fields.name.generate_default().generate()
        data = {'name': name, 'parent_id': self.get_id()}
        for key, value in kwargs.items():
            if value is not OMIT:
                data[key] = self.fields.get(key).binding.get_api_value_from_value(self.system, type(self), None, value)
        try:
            child = self._create(self.system, self.get_url_path(self.system), data=data,
                                 tags=self.get_tags_for_object_operations(self.system), parent=self)
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.entity_child_failure',
                                         {'obj': self, 'exception': e, 'system': self.system},
                                         tags=hook_tags)
                self.trigger_cancel_fork()
        self.trigger_finish_fork(child)
        gossip.trigger_with_tags('infinidat.sdk.post_entity_child_creation',
                                 {'source': self, 'target': child, 'system': self.system},
                                 tags=hook_tags)

        handle_possible_replication_snapshot(child)
        return child

    def delete(self, force_if_snapshot_locked=OMIT):  # pylint: disable=arguments-differ
        super().delete(force_if_snapshot_locked=force_if_snapshot_locked)

    def _is_synced_remote_entity(self):
        if not self.system.compat.has_sync_replication() or not self.is_rmr_target():
            return False
        if isinstance(self, self.system.filesystems.object_type):
            return False
        source_replica = self.get_replica().get_remote_replica(safe=True)
        return source_replica and source_replica.is_type_sync() and not source_replica.is_async_mode()

    def trigger_begin_fork(self):
        assert self._forked_obj is None
        if self._is_synced_remote_entity():
            remote_entity = self.get_remote_entity()
            if remote_entity is not None:
                self._forked_obj = self.get_remote_entity()
            else:
                _logger.debug('Could not fetch remote entity for {}. Forking local entity', self)
                self._forked_obj = self
        else:
            self._forked_obj = self
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags(_BEGIN_FORK_HOOK, {'obj': self._forked_obj}, tags=hook_tags)


    def trigger_cancel_fork(self):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags(_CANCEL_FORK_HOOK, {'obj': self._forked_obj}, tags=hook_tags)
        self._forked_obj = None

    def trigger_finish_fork(self, child):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags(_FINISH_FORK_HOOK, {'obj': self._forked_obj, 'child': child}, tags=hook_tags)
        self._forked_obj = None

    def create_snapshot(self, name=None, **kwargs):
        """Creates a snapshot from this entity, if supported by the system
        Supports passing name, write_protected and all other snapshots creation fields
        """
        return self._create_child(name, **kwargs)

    def restore(self, snapshot):
        """Restores this entity from a given snapshot object
        """
        snapshot_id = snapshot.id
        restore_url = self.get_this_url_path().add_path('restore')
        self.trigger_before_restore(snapshot)
        try:
            self.system.api.post(restore_url, data=snapshot_id)
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                self.trigger_restore_failure(snapshot, e)
        self.trigger_after_restore(snapshot)

    def trigger_before_restore(self, source):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.pre_object_restore', {'source': source, 'target': self}, tags=hook_tags)
        gossip.trigger_with_tags('infinidat.sdk.pre_data_restore', {'source': source, 'target': self}, tags=hook_tags)

    def trigger_restore_failure(self, source, e):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.data_restore_failure', {'source': source, 'target': self, 'exc': e},
                                 tags=hook_tags)
        gossip.trigger_with_tags('infinidat.sdk.object_restore_failure', {'source': source, 'target': self, 'exc': e},
                                 tags=hook_tags)

    def trigger_after_restore(self, source):
        hook_tags = self.get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.post_data_restore',
                                 {'source': source, 'target': self, 'require_real_data': False, 'reason': None},
                                 tags=hook_tags)
        gossip.trigger_with_tags('infinidat.sdk.post_object_restore', {'source': source, 'target': self},
                                 tags=hook_tags)

    def get_snapshots(self):
        """Retrieves all snapshot children of this entity
        """
        return self.get_children(type=self._get_snapshot_type())

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
        """Returns the space to be reclaimed if the dataset would be deleted according to delete simulation api
        """
        url = URL(self.get_url_path(self.system)).add_path('delete_simulation')
        res = self.system.api.post(url, data=dict(entities=[self.id]))
        return res.get_result()['space_reclaimable'] * byte

    @InfiniBoxObject.requires_cache_invalidation("pool")
    def move_pool(self, target_pool, with_capacity=False):
        """Moves this entity to a new pool, optionally along with its needed capacity
        """
        data = dict(pool_id=target_pool.get_id(), with_capacity=with_capacity)
        hook_tags = self.get_tags_for_object_operations(self.system)
        source_pool = self.get_pool()
        gossip.trigger_with_tags(
            'infinidat.sdk.pre_pool_move',
            {'obj': self, 'with_capacity': with_capacity, 'system': self.system,
             'target_pool': target_pool, 'source_pool': source_pool},
            tags=hook_tags)

        try:
            self.system.api.post(self.get_this_url_path().add_path('move'), data=data)
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.pool_move_failure', {
                    'obj': self,
                    'with_capacity': with_capacity,
                    'system': self.system,
                    'exception': e,
                    'target_pool': target_pool,
                    'source_pool': source_pool}, tags=hook_tags)

        gossip.trigger_with_tags(
            'infinidat.sdk.post_pool_move',
            {'obj': self, 'with_capacity': with_capacity, 'system': self.system,
             'target_pool': target_pool, 'source_pool': source_pool},
            tags=hook_tags)

    def get_replicas(self):
        if isinstance(self, self.system.types.filesystem) and not self.system.compat.has_nas_replication():
            return []
        if self.system.compat.get_version_as_float() >= 5.5 and \
            isinstance(self, self.system.types.volume) and self.is_in_cons_group():
            searched_id = self.get_cons_group().id
        else:
            searched_id = self.id
        return self.system.replicas.find(local_entity_id=searched_id).to_list()

    def get_replica(self):
        returned = self.get_replicas()
        if len(returned) > 1:
            raise TooManyObjectsFound('Replicas of {}'.format(self))
        elif len(returned) == 0:
            raise ObjectNotFound('Replicas of {}'.format(self))
        return returned[0]

    def get_remote_entities(self):
        returned = []
        for replica in self.get_replicas():
            remote_entity = replica.get_remote_data_entity_from_local(self)
            if remote_entity is not None:
                returned.append(remote_entity)
        return returned

    def get_remote_entity(self):
        returned = self.get_remote_entities()
        if len(returned) > 1:
            raise TooManyObjectsFound()
        elif len(returned) == 0:
            return None
        return returned[0]

    def is_replicated(self, from_cache=DONT_CARE):
        """Returns True if this volume is a part of a replica, whether as source or as target
        """
        fields = ['rmr_source', 'rmr_target']
        if self.system.compat.has_active_active():
            fields.append('rmr_active_active_peer')
        return any(self.get_fields(fields, from_cache=from_cache).values())

    def assign_qos_policy(self, qos_policy):
        assert self.system.compat.has_qos(), 'QoS is not supported in this version'
        qos_policy.assign_entity(self)

    def unassign_qos_policy(self, qos_policy):
        assert self.system.compat.has_qos(), 'QoS is not supported in this version'
        assert qos_policy == self.get_qos_policy(), 'QoS policy {} is not assigned to {}'.format(qos_policy, self)
        qos_policy.unassign_entity(self)
