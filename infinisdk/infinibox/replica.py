# pylint: disable=no-member
import logbook
import gossip
import functools
from ..core.utils import end_reraise_context
from ..core import Field, MillisecondsDatetimeType
from ..core.api.special_values import OMIT
from ..core.bindings import RelatedObjectNamedBinding, ReplicaEntityBinding
from ..core.exceptions import CannotGetReplicaState, InvalidUsageException, TooManyObjectsFound
from ..core.translators_and_types import MillisecondsDeltaType, CapacityType
from ..core.type_binder import TypeBinder
from ..core.system_object import SystemObject

_logger = logbook.Logger(__name__)

def require_sync_replication(func):
    @functools.wraps(func)
    def new_func(self, *args, **kwargs):
        if self.system.compat.has_sync_replication():
            return func(self, *args, **kwargs)
        raise NotImplementedError("not availble in this version")
    return new_func


class ReplicaBinder(TypeBinder):

    """Implements *system.replicas*
    """
    def replicate_volume(self, volume, remote_volume=None, **kw):
        """Convenience wrapper around :func:`ReplicaBinder.replicate_entity`

        :seealso: :meth:`.replicate_entity`
        """
        return self.replicate_entity(entity=volume, remote_entity=remote_volume, **kw)

    def replicate_cons_group(self, cg, remote_cg=None, remote_pool=OMIT, **kw):
        """Convenience wrapper around :func:`ReplicaBinder.replicate_entity`

        :seealso: :meth:`.replicate_entity`
        """
        return self.replicate_entity(entity=cg, remote_entity=remote_cg, remote_pool=remote_pool, **kw)


    def replicate_entity(self, entity, link, remote_pool=None, remote_entity=None, **kw):
        """Replicates a entity or CG, creating its remote replica on the specified pool

        :param remote_pool: if omitted, ``remote_entity`` must be specified. Otherwise, means creating target entity
        :param remote_entity: if omitted, ``remote_pool`` must be specified. Otherwise, means creating based on
                              existing entity on target
        :param member_mappings: required if remote_entity is specified and is a consistency group. This parameter is
                                a dictionary mapping local member entities to remote ones
        """
        if remote_entity is None:
            assert remote_pool is not None
            return self.replicate_entity_create_target(entity, link, remote_pool=remote_pool, **kw)
        return self.replicate_entity_existing_target(entity, link, remote_entity=remote_entity, **kw)

    def replicate_entity_create_target(self, entity, link, remote_pool=OMIT, remote_entity_names=OMIT, **kw):
        """Replicates an entity, creating its remote replica on the specified pool

        :param remote_pool: Remote pool to use for entity creation on the remote side
        :param remote_entity_names: A list or tuple containing the entity names created on remote side.
                                    In case of cg - controls the entity names, not the cg name.
        """
        if remote_entity_names is not OMIT:
            assert isinstance(remote_entity_names, (list, tuple)), "object remote_entity_names must be tuple or list"
        return self.system.replicas.create(link=link,
                                           entity_pairs=self._build_entity_pairs_create_target(remote_entity_names,
                                                                                               entity),
                                           remote_pool_id=remote_pool.id if remote_pool is not OMIT else OMIT,
                                           **self._get_extra_replica_kwargs(kw, entity))

    def replicate_entity_existing_target(self, entity, link, remote_entity, member_mappings=None, **kw):
        """Replicates an entity, using a formatted/empty entity on the other side

        :param remote_entity: Remote entity to use for replication
        :param member_mappings: required if remote_entity is specified and is a consistency group. This parameter is
                                a dictionary mapping local member entities to remote ones
        """
        entity_pairs = self._build_entity_pairs_existing(entity, remote_entity, member_mappings, use_snapshots=False)
        return self.system.replicas.create(link=link, entity_pairs=entity_pairs,
                                           **self._get_extra_replica_kwargs(kw, entity, remote_entity))

    def replicate_entity_use_base(self, entity, link, local_snapshot, remote_snapshot, member_mappings=None, **kw):
        """Replicates an entity, using an existing remote entity and a base snapthot on both sides

        :param local_snapshot: Local base snapshot to use
        :param remote_snapshot: Remote base snapshot to use
        :param member_mappings: required if remote_entity is specified and is a consistency group. This parameter is a
                                dictionary mapping local member entities to tuples of (local_snapshot, remote_snapshot)
        """
        entity_pairs = self._build_entity_pairs_existing(local_snapshot, remote_snapshot, member_mappings,
                                                         use_snapshots=True)
        creation_kwargs = self._get_extra_replica_kwargs(kw, entity, remote_entity=remote_snapshot.get_parent())
        return self.system.replicas.create(link=link, entity_pairs=entity_pairs, **creation_kwargs)

    def replicate_entity_take_snap(self, entity, link, remote_entity, member_mappings=None, **kw):
        """Replicates a entity, using the currently found data on both sides as a reference.

        :param entity: Local entity to use
        :param remote_entity: Remote entity to use
        :param member_mappings: required if remote_entity is specified and is a consistency group. This parameter is
                                a dictionary mapping local member entities to tuples of (entity, remote_entity)
        """
        entity_pairs = self._build_entity_pairs_existing(entity, remote_entity, member_mappings, use_snapshots=False,
                                                         take_snapshot=True)
        creation_kwargs = self._get_extra_replica_kwargs(kw, entity, remote_entity=remote_entity.get_parent())
        return self.system.replicas.create(link=link, entity_pairs=entity_pairs, **creation_kwargs)


    def _get_extra_replica_kwargs(self, kw, entity, remote_entity=None):
        returned = kw
        if 'base_action' in returned:
            raise InvalidUsageException("replicate_entity() doesn't support creating replica with base_action format")
        assert 'entity_type' not in returned
        assert 'local_cg_id' not in returned
        assert 'remote_cg_id' not in returned
        if isinstance(entity, entity.system.cons_groups.object_type):
            returned['entity_type'] = 'CONSISTENCY_GROUP'
            returned['local_cg_id'] = self._parent_or_entity_id(entity)
            if remote_entity is not None:
                returned['remote_cg_id'] = self._parent_or_entity_id(remote_entity)
        elif isinstance(entity, entity.system.filesystems.object_type):
            returned['entity_type'] = 'FILESYSTEM'
        else:
            returned['entity_type'] = 'VOLUME'
        return returned

    def _parent_or_entity_id(self, entity):
        parent = entity.get_parent(from_cache=True)
        if parent is not None:
            return parent.id
        return entity.id

    def _build_entity_pairs_create_target(self, remote_entity_names, entity):
        returned = []
        names_index = 0
        for sub_entity in self._get_sub_entities(entity):
            new_pair = {
                'remote_base_action': 'CREATE',
                'local_entity_id': sub_entity.id,
                'remote_entity_id': None,
                }
            if remote_entity_names is not OMIT and names_index < len(remote_entity_names):
                new_pair['remote_entity_name'] = remote_entity_names[names_index]
                names_index += 1
            returned.append(new_pair)
        return returned

    def _build_entity_pairs_existing(self, local_entity, remote_entity, member_mappings, use_snapshots,
                                     take_snapshot=False):
        if local_entity is None:
            raise InvalidUsageException("Local entity cannot be None")
        if remote_entity is None:
            raise InvalidUsageException("Remote entity cannot be None")

        returned = []
        if not member_mappings:
            if isinstance(local_entity, local_entity.system.cons_groups.object_type) and \
               len(local_entity.get_members()) > 0:
                raise InvalidUsageException('Specifying non-empty remote CG requires passing a `member_mappings` '
                                            'argument, mapping local member entities to remote entities')
            member_mappings = {local_entity: remote_entity}

        for sub_entity in self._get_sub_entities(local_entity):
            remote_sub_entity = member_mappings[sub_entity]
            if use_snapshots:
                returned.append({
                    'local_base_action': 'BASE',
                    'remote_base_action': 'BASE',
                    'local_entity_id': sub_entity.get_parent(from_cache=True).id,
                    'remote_entity_id': remote_sub_entity.get_parent(from_cache=True).id,
                    'local_base_entity_id': sub_entity.id,
                    'remote_base_entity_id': remote_sub_entity.id,
                })
            else:
                entity_pair = {
                    'remote_base_action': 'TAKE_SNAP' if take_snapshot else 'NO_BASE_DATA',
                    'local_entity_id': sub_entity.id,
                    'remote_entity_id': member_mappings[sub_entity].id,
                }
                if take_snapshot:
                    entity_pair['local_base_action'] = 'TAKE_SNAP'
                returned.append(entity_pair)
        return returned

    def _get_sub_entities(self, entity):
        if isinstance(entity, entity.system.cons_groups.object_type):
            return entity.get_members().to_list()
        return [entity]


class Replica(SystemObject):

    BINDER_CLASS = ReplicaBinder

    FIELDS = [

        Field('id', type=int, is_identity=True, is_filterable=True),
        Field('description', is_filterable=True, is_sortable=True, mutable=True),
        Field('updated_at', type=MillisecondsDatetimeType, is_filterable=True, is_sortable=True),
        Field('created_at', type=MillisecondsDatetimeType, is_filterable=True, is_sortable=True, cached=True),
        Field('link', api_name='link_id', binding=RelatedObjectNamedBinding('links'),
              type='infinisdk.infinibox.link:Link', creation_parameter=True),
        Field('entity_pairs', type=list, creation_parameter=True, optional=True),
        Field('entity_type', type=str, cached=True, creation_parameter=True, default='VOLUME', is_filterable=True),
        Field('remote_pool_id', type=int, creation_parameter=True, optional=True, is_filterable=True, is_sortable=True),
        Field('remote_replica_id', type=int, is_filterable=True, is_sortable=True, cached=True),
        Field('role', type=str, cached=False, is_filterable=True),
        Field('progress', type=int),
        Field('jobs', type=list, cached=False),
        Field('job_state'),
        Field('pending_job_count', type=int),
        Field('throughput', type=int),
        Field('restore_point', type=MillisecondsDatetimeType, is_filterable=True, is_sortable=True),
        Field('last_synchronized', type=MillisecondsDatetimeType),
        Field('last_replicated_guid', api_name='_consistent_guid', is_filterable=True, is_sortable=True),
        Field('state', type=str, cached=False, is_filterable=True),
        Field('state_description'),
        Field('state_reason'),
        Field('initial', api_name='is_initial', type=bool, cached=False),
        Field('sync_interval', api_name='sync_interval', type=MillisecondsDeltaType,
              mutable=True, creation_parameter=True, is_filterable=True, is_sortable=True, optional=True),
        Field('rpo', api_name='rpo_value', type=MillisecondsDeltaType, mutable=True,
              creation_parameter=True, is_filterable=True, is_sortable=True, optional=True),
        Field('rpo_state'),
        Field('rpo_type', is_filterable=True, is_sortable=True),
        Field('remote_cg_id', type=int, is_filterable=True, is_sortable=True, cached=True),
        Field('remote_cg_name', is_filterable=True, is_sortable=True),
        Field('local_cg_id', type=int, is_filterable=True, cached=True),
        Field('local_cg_name', is_filterable=True, is_sortable=True),
        Field('local_pool_id', type=int, is_filterable=True, is_sortable=True),
        Field('local_pool_name', is_filterable=True, is_sortable=True),
        Field('remote_pool_name', is_filterable=True, is_sortable=True),
        Field('staging_area_allocated_size', type=CapacityType),
        Field('replication_type', type=str, creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True, feature_name="sync_replication"),
        Field('sync_state', type=str, feature_name="sync_replication", cached=False, is_filterable=True),
        Field('sync_duration', type=int),
        Field('async_mode', type=bool, feature_name="sync_replication", cached=False),
        Field('latency', type=int, feature_name="sync_replication"),
        Field('domino', type=bool, is_filterable=True, is_sortable=True, feature_name="sync_replication"),
        Field('assigned_sync_remote_ips', type=list, api_name="_assigned_sync_remote_ips",
              feature_name="sync_replication"),
        Field('next_job_start_time', type=MillisecondsDatetimeType),
        Field('next_restore_point', type=MillisecondsDatetimeType),
        Field('permanent_failure_wait_interval', type=MillisecondsDeltaType, mutable=True,
              is_filterable=True, is_sortable=True),
        Field('temporary_failure_retry_interval', type=MillisecondsDeltaType, mutable=True,
              is_filterable=True, is_sortable=True),
        Field('temporary_failure_retry_count', type=int, mutable=True, is_filterable=True, is_sortable=True),
        Field('started_at', type=MillisecondsDatetimeType),
        Field('preferred', api_name='is_preferred', type=bool, optional=True, is_filterable=True, is_sortable=True,
              creation_parameter=True, mutable=False, feature_name="active_active_preferred_on_replica"),
        Field('local_entity', api_name='local_entity_id', binding=ReplicaEntityBinding(), creation_parameter=True,
              optional=True, is_filterable=True, is_sortable=True, feature_name="replica_auto_create",
              add_getter=False),
        Field('remote_entity', api_name='remote_entity_id', binding=ReplicaEntityBinding(), creation_parameter=True,
              optional=True, is_filterable=True, is_sortable=True, feature_name="replica_auto_create",
              add_getter=False),
        Field('local_entity_name', type=str, creation_parameter=True, optional=True, is_filterable=True,
              is_sortable=True, feature_name="replica_auto_create"),
        Field('remote_entity_name', type=str, creation_parameter=True, optional=True, is_filterable=True,
              is_sortable=True, feature_name="replica_auto_create"),
        Field('base_action', type=str, creation_parameter=True, optional=True,
              feature_name="replica_auto_create"),
        Field('concurrent_replica', type=bool, is_filterable=True, is_sortable=True,
              mutable=False, feature_name="concurrent_replication"),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_replication()

    def _get_entity_collection(self):
        if self.is_filesystem():
            return self.system.filesystems
        if self.is_volume():
            return self.system.volumes
        return self.system.cons_groups

    def _get_entity(self, is_local, from_cache=False, safe=False):
        system = self.system if is_local else self.get_remote_system(from_cache=from_cache, safe=safe)
        if system is None:
            return None
        side = 'local' if is_local else 'remote'

        if self.is_consistency_group():
            return system.cons_groups.get_by_id_lazy(self.get_field('{}_cg_id'.format(side)))

        pairs = self.get_entity_pairs(from_cache=True)
        if len(pairs) > 1:
            raise TooManyObjectsFound('Entity pairs for {}'.format(self))
        [pair] = pairs
        if self.is_filesystem():
            return system.filesystems.get_by_id_lazy(pair['{}_entity_id'.format(side)])
        else:
            return system.volumes.get_by_id_lazy(pair['{}_entity_id'.format(side)])

    def get_local_entity(self):
        """Returns the local entity used for replication, be it a volume, filesystem or a consistency group
        """
        return self._get_entity(is_local=True)

    def _get_entity_tags(self):
        if self.is_consistency_group():
            return ['cons_group']

        if self.is_filesystem():
            return ['filesystem']
        else:
            return ['volume']

    @staticmethod
    def _notify_pre_exposure(replica):
        if replica is None or not replica.is_in_system():
            return

        gossip.trigger_with_tags(
            'infinidat.sdk.pre_replication_snapshot_expose',
            {'source': replica.get_local_entity(), 'system': replica.system}, tags=replica._get_entity_tags())  # pylint: disable=protected-access

    @staticmethod
    def _notify_exposure_failure(replica, exception):
        if replica is None or not replica.is_in_system():
            return

        gossip.trigger_with_tags('infinidat.sdk.replication_snapshot_expose_failure',
                                 {'obj': replica, 'exception': exception, 'system': replica.system},
                                 tags=replica._get_entity_tags())  # pylint: disable=protected-access

    @staticmethod
    def _notify_post_exposure(replica, snapshot):
        if replica is None or not replica.is_in_system():
            return

        gossip.trigger_with_tags(
            'infinidat.sdk.post_replication_snapshot_expose',
            {'source': replica.get_local_entity(), 'snapshot': snapshot, 'system': replica.system},
            tags=replica._get_entity_tags())  # pylint: disable=protected-access

    def expose_last_consistent_snapshot(self):
        self._notify_pre_exposure(self)

        try:
            resp = self.system.api.post(
                self.get_this_url_path().add_path('expose_last_consistent_snapshot')).get_result()
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                self._notify_exposure_failure(self, e)

        if self.is_consistency_group():
            snapshot_id = resp['_local_reclaimed_sg_id']
        else:
            snapshot_id = resp['entity_pairs'][0]['_local_reclaimed_snapshot_id']
        if snapshot_id is None:
            return None
        returned = self._get_entity_collection().get_by_id_lazy(snapshot_id)
        gossip.trigger_with_tags('infinidat.sdk.replica_snapshot_created',
                                 {'snapshot': returned, 'replica_deleted': False},
                                 tags=['infinibox'])
        self._notify_post_exposure(self, returned)
        return returned


    def get_local_volume(self):
        """Returns the local volume, assuming there is exactly one
        """
        if not self.is_volume():
            raise NotImplementedError('get_local_volume() is not supported on a {} replication'.format(self.get_entity_type())) # pragma: no cover  # pylint: disable=line-too-long

        return self.get_local_entity()

    def get_local_filesystem(self):
        """Returns the local volume, assuming there is exactly one
        """
        if not self.is_filesystem():
            raise NotImplementedError('get_local_filesystem() is not supported on a {} replication'.format(self.get_entity_type())) # pragma: no cover  # pylint: disable=line-too-long

        return self.get_local_entity()

    def get_local_cg(self):
        """Returns the local cg, assuming this is a consistency group replica
        """
        if not self.is_consistency_group():
            raise NotImplementedError('get_local_cg() is not supported on a {} replication'.format(self.get_entity_type())) # pragma: no cover  # pylint: disable=line-too-long

        return self.get_local_entity()

    def get_local_data_entities(self):
        """Returns all local volumes, whether as part of a consistency group, filesystem or a single volume
        """
        if self.is_consistency_group():
            return self.get_local_entity().get_members().to_list()
        return [self.get_local_entity()]

    def get_remote_data_entities(self, from_cache=False):
        """Returns all local volumes, whether as part of a consistency group, filesystem or a single volume
        """
        if self.is_consistency_group():
            return self.get_remote_entity(from_cache=from_cache).get_members().to_list()
        return [self.get_remote_entity(from_cache=from_cache)]

    def get_remote_data_entity_from_local(self, dataset):
        remote_system = self.get_remote_system(from_cache=True)
        if remote_system is None:
            return None
        collection = remote_system.objects.get_binder_by_type_name(dataset.get_type_name())
        for pair in self.get_entity_pairs(from_cache=True):
            if pair['local_entity_id'] == dataset.id:
                return collection.get_by_id_lazy(pair['remote_entity_id'])

    def is_consistency_group(self):
        """Returns whether this replica is configured with a consistency group as a local entity
        """
        return self.get_entity_type(from_cache=True).lower() == 'consistency_group'


    def is_volume(self):
        """Returns True if this replica replicates a single volume entity
        """
        return self.get_entity_type(from_cache=True).lower() == 'volume'


    def is_filesystem(self):
        """Returns True if this replica replicates a single filesystem entity
        """
        return self.get_entity_type(from_cache=True).lower() == 'filesystem'


    def suspend(self):
        """Suspends this replica
        """
        gossip.trigger_with_tags('infinidat.sdk.pre_replica_suspend', {'replica': self}, tags=['infinibox'])
        try:
            self.system.api.post(self.get_this_url_path().add_path('suspend'))
        except Exception as e: # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.replica_suspend_failure',
                                         {'replica': self, 'exception': e}, tags=['infinibox'])
        gossip.trigger_with_tags('infinidat.sdk.post_replica_suspend', {'replica': self}, tags=['infinibox'])
        self.invalidate_cache('state')

    def sync(self):
        """Starts a sync job
        """
        returned = self.system.api.post(self.get_this_url_path().add_path('sync'),
                                        headers={'X-INFINIDAT-RAW-RESPONSE': 'true'})
        result = returned.get_result()
        return result

    def resume(self):
        """Resumes this replica
        """
        gossip.trigger_with_tags('infinidat.sdk.pre_replica_resume', {'replica': self}, tags=['infinibox'])
        try:
            self.system.api.post(self.get_this_url_path().add_path('resume'))
        except Exception as e: # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.replica_resume_failure',
                                         {'replica': self, 'exception': e}, tags=['infinibox'])
        gossip.trigger_with_tags('infinidat.sdk.post_replica_resume', {'replica': self}, tags=['infinibox'])
        self.invalidate_cache('state')

    @require_sync_replication
    def switch_role(self):
        """Switches replica role - sync replicas only
        """
        gossip.trigger_with_tags('infinidat.sdk.pre_replica_switch_role', {'replica': self}, tags=['infinibox'])
        try:
            self.system.api.post(self.get_this_url_path().add_path('switch_role'))
        except Exception as e: # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.replica_switch_role_failure',
                                         {'replica': self, 'exception': e}, tags=['infinibox'])
        gossip.trigger_with_tags('infinidat.sdk.post_replica_switch_role', {'replica': self}, tags=['infinibox'])
        self.invalidate_cache()

    def is_type_sync(self):
        if self.system.compat.has_sync_replication():
            return self.get_replication_type().lower() == 'sync'
        return False


    def is_type_active_active(self):
        if self.system.compat.has_sync_replication():
            return self.get_replication_type(from_cache=True).lower() == 'active_active'
        return False

    def is_type_async(self):
        if self.system.compat.has_sync_replication():
            return self.get_replication_type().lower() == 'async'
        return True

    def _is_in_sync_state(self, *sync_states):
        current_sync_state = self.get_sync_state()
        return current_sync_state and current_sync_state.lower() in sync_states

    def _is_in_state(self, *states):
        current_state = self.get_state()
        return current_state and current_state.lower() in states

    def _get_state_lower(self, **kwargs):
        return str(self.get_state(**kwargs)).lower()

    def is_synchronized(self):
        """Returns True if this replica sync state is 'SYNCHRONIZED'
         """
        return self._is_in_sync_state('synchronized')

    def is_sync_in_progress(self):
        """Returns True if this replica sync state is 'SYNC_IN_PROGRESS'
         """
        return self._is_in_sync_state('sync_in_progress')

    def is_initializing(self):
        """Returns True if the replica sync state is 'INITIALIZING'
         """
        return self._is_in_sync_state('initializing')

    def is_initializing_pending(self):
        """Returns True if the replica sync state is 'INITIALIZING_PENDING'
         """
        return self._is_in_sync_state('initializing_pending')

    def is_out_of_sync(self):
        """Returns True if the replica sync state is 'OUT_OF_SYNC'
         """
        return self._is_in_sync_state('out_of_sync')

    @require_sync_replication
    def change_type_to_async(self, params=None):
        """Changes the replication type to ASYNC

        :param params: Optional dictionary containing additional parameters for the type change
         """
        self._change_type(new_type='async', params=params)

    @require_sync_replication
    def change_type_to_sync(self, params=None):
        """Changes the replication type to SYNC

        :param params: Optional dictionary containing additional parameters for the type change
         """
        self._change_type(new_type='sync', params=params)

    def _change_type(self, new_type, params=None):
        if params is None:
            params = {}
        old_type = self.get_replication_type().lower()
        new_type = new_type.lower()
        gossip.trigger_with_tags('infinidat.sdk.pre_replica_change_type',
                                 {'replica': self, 'old_type': old_type, 'new_type': new_type},
                                 tags=['infinibox'])
        try:
            url = self.get_this_url_path().add_path('change_type_to_async') if new_type == 'async' \
                  else self.get_this_url_path().add_path('change_type_to_sync')
            self.system.api.post(url, data=params)
        except Exception as e: # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.replica_change_type_failure',
                                         {'replica': self, 'old_type': old_type, 'new_type': new_type, 'exception': e},
                                         tags=['infinibox'])
        gossip.trigger_with_tags('infinidat.sdk.post_replica_change_type',
                                 {'replica': self, 'old_type': old_type, 'new_type': new_type},
                                 tags=['infinibox'])
        self.invalidate_cache()

    def _validate_can_check_state(self):
        if self.is_target():
            raise CannotGetReplicaState('Replica state cannot be checked on target replica')

    def is_suspended(self, **kwargs):
        """Returns whether or not this replica is currently suspended
        """
        if self.is_type_active_active():
            return False
        self._validate_can_check_state()
        return self._is_in_state('suspended', 'auto_suspended', **kwargs)

    def is_user_suspended(self, **kwargs):
        """Returns whether or not this replica is currently suspended due to a user request
        """
        if self.is_type_active_active():
            return False
        self._validate_can_check_state()
        return self._is_in_state('suspended', **kwargs)

    def is_idle(self, **kwargs):
        """Returns whether or not this replica is in idle state
        """
        self._validate_can_check_state()
        if self.system.compat.has_sync_job_states():
            return not self.is_replicating() and not self.is_initial_replication()\
                and not self.is_stalled() and self.is_active()
        return self._is_in_state('idle', **kwargs)

    def is_lagging(self, **kwargs):
        if self.is_type_active_active():
            return self._is_in_sync_state("lagging", **kwargs)
        return False

    def is_auto_suspended(self, **kwargs):
        """Returns whether or not this replica is in auto_suspended state
        """
        if self.is_type_active_active():
            return False
        self._validate_can_check_state()
        return self._is_in_state('auto_suspended', **kwargs)

    def is_initial_replication(self, **kwargs):
        """Returns whether or not this replica is in initiating state
        """
        if self.is_type_active_active():
            return self._is_in_sync_state("initializing", "initializing_pending", **kwargs)
        self._validate_can_check_state()
        if self.system.compat.has_sync_job_states():
            return self.is_initial(**kwargs) and self._any_sync_job_state_contains(['initializing', 'stalled'])
        return 'initial' in self._get_state_lower(**kwargs)

    def is_pending(self, **kwargs):
        """Returns whether or not this replication is waiting to start initializing
        """
        self._validate_can_check_state()
        if not self.system.compat.has_sync_job_states():
            raise NotImplementedError("This system ({}) doesn't support replica \"pending\" state".format(self.system))
        return self.is_active(**kwargs) and self._any_sync_job_state_contains('pending')

    def _get_jobs(self):
        returned = self.get_field('jobs')
        if not returned:
            returned = []
        global_job_state = None
        for j in returned:
            if j.get('state') is None:
                # workaround for several cases where state isn't reported
                if global_job_state is None:
                    global_job_state = self.get_field('job_state')
                j['state'] = global_job_state
        return returned

    def is_replicating(self, **kwargs):
        """Returns whether or not this replica is in replicating state
        """
        self._validate_can_check_state()
        if self.system.compat.has_sync_job_states():
            return self.is_active() and self._any_sync_job_state_contains('replicating')
        return self._is_in_state('replicating', **kwargs)

    def is_stalled(self, **kwargs):
        if self.is_type_active_active():
            return self._is_in_sync_state("sync_stalled", **kwargs)
        self._validate_can_check_state()
        if not self.system.compat.has_sync_job_states():
            raise NotImplementedError("Checking for stalled is not supported on systems without sync job states")
        return self._any_sync_job_state_contains('stalled')

    def is_active(self, **kwargs):
        """Returns whether or not the replica is currently active
        """
        if self.is_type_active_active():
            return self._is_in_sync_state('synchronized', 'initializing',
                                          'initializing_pending', 'sync_in_progress',
                                          **kwargs)
        self._validate_can_check_state()
        state = self._get_state_lower(**kwargs)
        if self.system.compat.has_sync_job_states():
            return state == 'active'
        return state in ['idle', 'initiating', 'initial_replication', 'replicating']

    def change_role(self, entity_pairs=OMIT):
        """Changes the role of this replica from source to target or vice-versa
        """
        data = {'entity_pairs': entity_pairs} if entity_pairs is not OMIT else None
        gossip.trigger_with_tags('infinidat.sdk.pre_replica_change_role', {'replica': self}, tags=['infinibox'])
        try:
            self.system.api.post(self.get_this_url_path().add_path('change_role'), data=data)
        except Exception as e: # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.replica_change_role_failure',
                                         {'replica': self, 'exception': e}, tags=['infinibox'])
        gossip.trigger_with_tags('infinidat.sdk.post_replica_change_role', {'replica': self}, tags=['infinibox'])
        self.invalidate_cache()

    def is_source(self, *args, **kwargs):
        """A predicate returning whether or not the replica is currently in the "source" role
        """
        if self.is_type_active_active():
            return False
        return self.get_role(*args, **kwargs).lower() == 'source'

    def is_target(self, *args, **kwargs):
        """A predicate returning whether or not the replica is currently in the "target" role
        """
        if self.is_type_active_active():
            return False
        return not self.is_source(*args, **kwargs)

    def has_local_entity(self, entity):
        pairs = self.get_field('entity_pairs', from_cache=True)
        for pair in pairs:
            if pair['local_entity_id'] == entity.id:
                return True
        return False

    def _should_retain_staging_area(self, retain_value=OMIT):
        if retain_value is not OMIT:
            return retain_value
        return self.system.compat.has_replica_auto_create()

    # pylint: disable=arguments-differ
    def delete(self, retain_staging_area=OMIT, force_if_remote_error=OMIT, force_on_target=OMIT,
               force_if_no_remote_credentials=OMIT, force_on_local=OMIT, keep_serial_on_local=OMIT):
        """Deletes this replica
        """
        path = self.get_this_url_path()
        requested_retain_staging_area = retain_staging_area
        remote_replica = self.get_remote_replica(safe=True)
        if remote_replica is None:
            _logger.debug('Failed to get remote replica during delete operation')
        retain_staging_area = self._should_retain_staging_area(retain_value=retain_staging_area)
        if retain_staging_area:
            self._notify_pre_exposure(self)
            self._notify_pre_exposure(remote_replica)

        try:
            resp = self._send_delete_with_hooks_tirggering(
                path,
                force_if_remote_error=force_if_remote_error,
                force_on_target=force_on_target,
                force_if_no_remote_credentials=force_if_no_remote_credentials,
                force_on_local=force_on_local,
                keep_serial_on_local=keep_serial_on_local,
                retain_staging_area=requested_retain_staging_area)
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                if retain_staging_area:
                    self._notify_exposure_failure(self, e)
                    self._notify_exposure_failure(remote_replica, e)

        result = resp.get_result()
        entity_pairs = result.get('entity_pairs') if result else None
        gossip.trigger_with_tags('infinidat.sdk.replica_deleted',
                                 {'replica': self, 'entity_pairs': entity_pairs, 'deletion_params': path.query_dict},
                                 tags=['infinibox'])

        if retain_staging_area:
            local, remote = self._get_deletion_result(resp.get_result(), remote_replica)
        else:
            local = remote = None
        for replica, snap in (self, local), (remote_replica, remote):
            if snap is not None:
                gossip.trigger_with_tags(
                    'infinidat.sdk.replica_snapshot_created', {'snapshot': snap, 'replica_deleted': True},
                    tags=['infinibox'])

                self._notify_post_exposure(replica, snap)
        return local, remote

    def _any_sync_job_state_contains(self, states):
        if not isinstance(states, list):
            states = [states]
        for state in states:
            state = state.lower()
            for sync_job in self._get_jobs():
                if sync_job['state'] is not None and state == sync_job['state'].lower():
                    return True
        return False

    def _get_deletion_result(self, result, remote_replica):
        if not result or 'entity_type' not in result:
            return None, None

        if 'group' in result['entity_type'].lower():

            return self._get_local_remote_snapshots(result, 'cons_groups', remote_replica, '_{0}_reclaimed_sg_id')

        [entity_pair] = result.get('entity_pairs', [None])
        if entity_pair is not None:
            collection_name = 'volumes' if result['entity_type'] != 'FILESYSTEM' else 'filesystems'
            return self._get_local_remote_snapshots(entity_pair, collection_name, remote_replica,
                                                    '_{0}_reclaimed_snapshot_id')
        return None, None

    def _get_local_remote_snapshots(self, result, collection_name, remote_replica, field_name_template):
        local_reclaimed_id = result.get(field_name_template.format('local'))
        if local_reclaimed_id is None:
            _logger.debug('Could not get local reclaimed id (missing {} in {})',
                          field_name_template.format('local'), result)
        remote_reclaimed_id = result.get(field_name_template.format('remote'))
        if remote_reclaimed_id is None:
            _logger.debug('Could not get remote reclaimed id (missing {} in {})',
                          field_name_template.format('remote'), result)

        local = remote = None

        if local_reclaimed_id is not None:
            local = getattr(self.system, collection_name).get_by_id_lazy(local_reclaimed_id)
        if remote_replica is not None and remote_reclaimed_id is not None:
            remote = getattr(remote_replica.system, collection_name).get_by_id_lazy(remote_reclaimed_id)
        return local, remote

    def get_remote_system(self, from_cache=True, safe=False):
        return self.get_link(from_cache=from_cache).get_linked_system(from_cache=from_cache, safe=safe)

    def get_remote_replica(self, from_cache=False, safe=False):
        """Get the corresponsing replica object in the remote machine. For this to work, the SDK user should
        call the register_related_system method of the Infinibox object when a link to a remote system is consructed
        for the first time"""
        linked_system = self.get_remote_system(from_cache=from_cache, safe=safe)
        if linked_system is None:
            return None
        return linked_system.replicas.get_by_id_lazy(self.get_remote_replica_id(from_cache=from_cache))

    def get_remote_entity(self, from_cache=False, safe=False):
        """Fetches the remote replicated entity if available
        """
        return self._get_entity(is_local=False, from_cache=from_cache, safe=safe)

    def get_remote_entity_pairs(self):
        """Returns the entity_pairs configuration as held by the remote replica

        .. note:: this uses the remote command execution API to run the command over the inter-system
          link
        """
        return self.system.api.get('remote/{}/api/rest/replicas/{}'.format(
            self.get_link().id,
            self.get_remote_replica_id(from_cache=True))).get_result()['entity_pairs']
