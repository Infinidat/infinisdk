# pylint: disable=no-member
from datetime import timedelta

import logbook

import gossip

from ..core import Field, MillisecondsDatetimeType
from ..core.api.special_values import OMIT
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import (CannotGetReplicaState, InvalidUsageException, TooManyObjectsFound, UnknownSystem)
from ..core.translators_and_types import MillisecondsDeltaType
from ..core.type_binder import TypeBinder
from .system_object import InfiniBoxObject

_logger = logbook.Logger(__name__)

class ReplicaBinder(TypeBinder):

    """Implements *system.replicas*
    """
    def replicate_volume(self, volume, remote_volume=None, **kw):
        """Convenience wrapper around :func:`ReplicaBinder.replicate_entity`

        :seealso: :meth:`.replicate_entity`
        """
        return self.replicate_entity(entity=volume, remote_entity=remote_volume, **kw)

    def replicate_cons_group(self, cg, remote_cg=None, **kw):
        """Convenience wrapper around :func:`ReplicaBinder.replicate_entity`

        :seealso: :meth:`.replicate_entity`
        """
        return self.replicate_entity(entity=cg, remote_entity=remote_cg, **kw)


    def replicate_entity(self, entity, link, remote_pool=None, remote_entity=None, **kw):
        """Replicates a entity or CG, creating its remote replica on the specified pool

        :param remote_pool: if omitted, ``remote_entity`` must be specified. Otherwise, means creating target entity
        :param remote_entity: if omitted, ``remote_pool`` must be specified. Otherwise, means creating based on existing entity on target
        :param member_mappings: required if remote_entity is specified and is a consistency group. This parameter is a dictionary mapping local member entities to remote ones
        """
        if remote_entity is None:
            assert remote_pool is not None
            return self.replicate_entity_create_target(entity, link, remote_pool=remote_pool, **kw)
        return self.replicate_entity_existing_target(entity, link, remote_entity=remote_entity, **kw)

    def replicate_entity_create_target(self, entity, link, remote_pool, **kw):
        """Replicates an entity, creating its remote replica on the specified pool

        :param remote_pool: Remote pool to use for entity creation on the remote side
        """
        return self.system.replicas.create(link=link, entity_pairs=self._build_entity_pairs_create_target(entity),
                                           remote_pool_id=remote_pool.id if remote_pool is not OMIT else OMIT,
                                           **self._get_extra_replica_kwargs(kw, entity))

    def replicate_entity_existing_target(self, entity, link, remote_entity, member_mappings=None, **kw):
        """Replicates an entity, using a formatted/empty entity on the other side

        :param remote_entity: Remote entity to use for replication
        :param member_mappings: required if remote_entity is specified and is a consistency group. This parameter is a dictionary mapping local member entities to remote ones
        """
        return self.system.replicas.create(link=link, entity_pairs=self._build_entity_pairs_existing(entity, remote_entity, member_mappings, use_snapshots=False),
                                           **self._get_extra_replica_kwargs(kw, entity, remote_entity))

    def replicate_entity_use_base(self, entity, link, local_snapshot, remote_snapshot, member_mappings=None, **kw):
        """Replicates an entity, using an existing remote entity and a base snapthot on both sides

        :param local_snapshot: Local base snapshot to use
        :param remote_snapshot: Remote base snapshot to use
        :param member_mappings: required if remote_entity is specified and is a consistency group. This parameter is a dictionary mapping local member entities to tuples of (local_snapshot, remote_snapshot)
        """
        return self.system.replicas.create(link=link, entity_pairs=self._build_entity_pairs_existing(local_snapshot, remote_snapshot, member_mappings, use_snapshots=True),
                                           **self._get_extra_replica_kwargs(kw, entity, remote_entity=remote_snapshot.get_parent()))

    def replicate_entity_take_snap(self, entity, link, remote_entity, member_mappings=None, **kw):
        """Replicates a entity, using the currently found data on both sides as a reference.

        :param entity: Local entity to use
        :param remote_entity: Remote entity to use
        :param member_mappings: required if remote_entity is specified and is a consistency group. This parameter is a dictionary mapping local member entities to tuples of (entity, remote_entity)
        """
        return self.system.replicas.create(link=link, entity_pairs=self._build_entity_pairs_existing(entity, remote_entity, member_mappings, use_snapshots=False, take_snapshot=True),
                                           **self._get_extra_replica_kwargs(kw, entity, remote_entity=remote_entity.get_parent()))


    def _get_extra_replica_kwargs(self, kw, entity, remote_entity=None):
        returned = kw
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

    def _build_entity_pairs_create_target(self, entity):
        returned = []
        for sub_entity in self._get_sub_entities(entity):
            returned.append({
                'remote_base_action': 'CREATE',
                'local_entity_id': sub_entity.id,
                'remote_entity_id': None,
                })
        return returned

    def _build_entity_pairs_existing(self, local_entity, remote_entity, member_mappings, use_snapshots, take_snapshot=False):
        returned = []
        if not member_mappings:
            if isinstance(local_entity, local_entity.system.cons_groups.object_type) and len(local_entity.get_members()) > 0:
                raise InvalidUsageException('Specifying non-empty remote CG requires passing a `member_mappings` argument, mapping local member entities to remote entities')
            member_mappings = {local_entity: remote_entity}

        for sub_entity in self._get_sub_entities(local_entity):
            remote_sub_entity = member_mappings[sub_entity]
            if use_snapshots:
                returned.append({
                    'local_base_action': 'BASE',
                    'remote_base_action': 'TAKE_SNAP' if take_snapshot else 'BASE',
                    'local_entity_id': sub_entity.get_parent(from_cache=True).id,
                    'remote_entity_id': remote_sub_entity.get_parent(from_cache=True).id,
                    'local_base_entity_id': sub_entity.id,
                    'remote_base_entity_id': remote_sub_entity.id,
                })
            else:
                returned.append({
                    'remote_base_action': 'NO_BASE_DATA',
                    'local_entity_id': sub_entity.id,
                    'remote_entity_id': member_mappings[sub_entity].id,
                })

        return returned

    def _get_sub_entities(self, entity):
        if isinstance(entity, entity.system.cons_groups.object_type):
            return entity.get_members().to_list()
        return [entity]


class Replica(InfiniBoxObject):

    BINDER_CLASS = ReplicaBinder

    FIELDS = [

        Field('id', type=int, is_identity=True),
        Field('link', api_name='link_id', binding=RelatedObjectBinding(
            'links'), type='infinisdk.infinibox.link:Link', creation_parameter=True),
        Field('entity_pairs', type=list, creation_parameter=True),
        Field('entity_type', type=str,
              creation_parameter=True, default='VOLUME'),
        Field('remote_pool_id', type=int,
              creation_parameter=True, optional=True),
        Field('remote_replica_id', type=int),
        Field('role', type=str, cached=False),
        Field('progress', type=int),
        Field('jobs', type=list, cached=False),
        Field('restore_point', type=MillisecondsDatetimeType),
        Field('last_synchronized', type=int),
        Field('last_replicated_guid', api_name='_consistent_guid'),
        Field('state', type=str, cached=False),
        Field('sync_interval', api_name='sync_interval', type=MillisecondsDeltaType,
              mutable=True,
              creation_parameter=True, default=timedelta(seconds=4)),

        Field('rpo', api_name='rpo_value', type=MillisecondsDeltaType, mutable=True),
        Field('rpo_state'),

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

    def get_local_entity(self):
        """Returns the local entity used for replication, be it a volume or a consistency group.
        """
        if self.is_consistency_group():
            return self.system.cons_groups.get_by_id_lazy(self.get_field('local_cg_id'))

        pairs = self.get_entity_pairs(from_cache=True)
        if len(pairs) > 1:
            raise TooManyObjectsFound('Entity pairs for {}'.format(self))
        [pair] = pairs
        if self.is_filesystem():
            return self.system.filesystems.get_by_id_lazy(pair['local_entity_id'])
        else:
            return self.system.volumes.get_by_id_lazy(pair['local_entity_id'])

    def expose_last_consistent_snapshot(self):
        resp = self.system.api.post(self.get_this_url_path().add_path('expose_last_consistent_snapshot')).get_result()
        if self.is_consistency_group():
            snapshot_id = resp['_local_reclaimed_sg_id']
        else:
            snapshot_id = resp['entity_pairs'][0]['_local_reclaimed_snapshot_id']
        if snapshot_id is None:
            return None
        returned = self._get_entity_collection().get_by_id_lazy(snapshot_id)
        gossip.trigger_with_tags(
                'infinidat.sdk.replica_snapshot_created', {'snapshot': returned}, tags=['infinibox'])

        return returned


    def get_local_volume(self):
        """Returns the local volume, assuming there is exactly one
        """
        if self.is_consistency_group():
            raise NotImplementedError('get_local_volume() is not supported on a consistency group replication') # pragma: no cover

        return self.get_local_entity()

    def get_local_cg(self):
        """Returns the local cg, assuming this is a consistency group replica
        """
        if not self.is_consistency_group():
            raise NotImplementedError('get_local_volume() is not supported on a consistency group replication') # pragma: no cover

        return self.get_local_entity()

    def get_local_cg_id(self):
        if not self.is_consistency_group():
            return None
        return self.get_local_entity().id


    def get_local_data_entities(self):
        """Returns all local volumes, whether as part of a consistency group or a single volume
        """
        if self.is_consistency_group():
            return self.get_local_entity().get_members().to_list()
        return [self.get_local_entity()]

    def is_consistency_group(self):
        """Returns whether this replica is configured with a consistency group as a local entity
        """
        return self.get_entity_type(from_cache=True).lower() == 'consistency_group'


    def is_volume(self):
        """Returns True if this replica replicates a single volume entity
        """
        return self.get_entity_type(from_cache=True).lower() == 'volume'


    def is_filesystem(self):
        """Returns True if this replica replicates a single volume entity
        """
        return self.get_entity_type(from_cache=True).lower() == 'filesystem'


    def suspend(self):
        """Suspends this replica
        """
        self.system.api.post(self.get_this_url_path().add_path('suspend'))
        self.invalidate_cache('state')

    def sync(self):
        """Starts a sync job
        """
        returned = self.system.api.post(self.get_this_url_path().add_path('sync'), headers={'X-INFINIDAT-RAW-RESPONSE': 'true'})
        return returned.get_result()

    def resume(self):
        """Resumes this replica
        """
        self.system.api.post(self.get_this_url_path().add_path('resume'))
        self.invalidate_cache('state')

    def _validate_can_check_state(self):
        if self.is_target():
            raise CannotGetReplicaState('Replica state cannot be checked on target replica')

    def is_suspended(self, *args, **kwargs):
        """Returns whether or not this replica is currently suspended
        """
        self._validate_can_check_state()
        return self.get_state(*args, **kwargs).lower() in ['suspended', 'auto_suspended']

    def is_user_suspended(self, *args, **kwargs):
        """Returns whether or not this replica is currently suspended due to a user request
        """
        self._validate_can_check_state()
        return self.get_state(*args, **kwargs).lower() == 'suspended'

    def is_idle(self, *args, **kwargs):
        """Returns whether or not this replica is in idle state
        """
        self._validate_can_check_state()
        if self.system.compat.has_sync_job_states():
            return all(sync_job['state'].lower() == 'done' or sync_job['state'].lower() == 'pending' for sync_job in self._get_jobs())
        return self.get_state(*args, **kwargs).lower() == 'idle'

    def is_auto_suspended(self, *args, **kwargs):
        """Returns whether or not this replica is in auto_suspended state
        """
        self._validate_can_check_state()
        return self.get_state(*args, **kwargs).lower() == 'auto_suspended'

    def is_initial_replication(self, *args, **kwargs):
        """Returns whether or not this replica is in initiating state
        """
        self._validate_can_check_state()
        if self.system.compat.has_sync_job_states():
            for job in self._get_jobs():
                if job['is_initial'] and job['state'].lower() != 'done':
                    return True
            return False
        return 'initial' in self.get_state(*args, **kwargs).lower()

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

    def is_replicating(self, *args, **kwargs):
        """Returns whether or not this replica is in replicating state
        """
        self._validate_can_check_state()
        if self.system.compat.has_sync_job_states():
            return self.is_active() and self._any_sync_job_state_contains('replicating')
        return self.get_state(*args, **kwargs).lower() == 'replicating'

    def is_stalled(self):
        self._validate_can_check_state()
        if not self.system.compat.has_sync_job_states():
            raise NotImplementedError("Checking for stalled is not supported on systems without sync job states")
        return self._any_sync_job_state_contains('stall')

    def is_active(self, *args, **kwargs):
        self._validate_can_check_state()
        if self.system.compat.has_sync_job_states():
            return self.get_state().lower() == 'active'
        return self.get_state(*args, **kwargs).lower() in ['idle', 'initiating', 'initial_replication', 'replicating']

    def change_role(self, entity_pairs=OMIT):
        data = {'entity_pairs': entity_pairs} if entity_pairs is not OMIT else None
        self.system.api.post(self.get_this_url_path()
                                 .add_path('change_role'), data=data)
        self.invalidate_cache()
        gossip.trigger_with_tags('infinidat.sdk.replica_after_change_role', {'replica': self}, tags=['infinibox'])

    def is_source(self, *args, **kwargs):
        return self.get_role(*args, **kwargs).lower() == 'source'

    def is_target(self, *args, **kwargs):
        return not self.is_source(*args, **kwargs)

    def has_local_entity(self, entity):
        pairs = self.get_field('entity_pairs', from_cache=True)
        for pair in pairs:
            if pair['local_entity_id'] == entity.id:
                return True
        return False

    def delete(self, retain_staging_area=False, force_if_remote_error=False, force_on_target=False, force_if_no_remote_credentials=False): # pylint: disable=arguments-differ
        path = self.get_this_url_path()
        if retain_staging_area:
            path = path.add_query_param('retain_staging_area', 'true')
        if force_if_remote_error:
            path = path.add_query_param('force_if_remote_error', 'true')
        if force_on_target:
            path = path.add_query_param('force_on_target', 'true')
        if force_if_no_remote_credentials:
            path = path.add_query_param('force_if_no_remote_credentials', 'true')

        try:
            remote_replica = self.get_remote_replica()
        except UnknownSystem:
            remote_replica = None

        with self._get_delete_context():
            resp = self.system.api.delete(path)

        if retain_staging_area:
            local, remote = self._get_deletion_result(resp.get_result(), remote_replica)
        else:
            local = remote = None
        for snap in local, remote:
            if snap is not None:
                gossip.trigger_with_tags(
                    'infinidat.sdk.replica_snapshot_created', {'snapshot': snap}, tags=['infinibox'])
        return local, remote

    def _any_sync_job_state_contains(self, substr):
        substr = substr.lower()
        for sync_job in self._get_jobs():
            if substr in sync_job['state'].lower():
                return True
        return False

    def _get_deletion_result(self, result, remote_replica):
        if not result or 'entity_type' not in result:
            return None, None

        if 'group' in result['entity_type'].lower():

            return self._get_local_remote_snapshots(result, 'cons_groups', remote_replica, '_{0}_reclaimed_sg_id')

        [entity_pair] = result.get('entity_pairs', [None])
        if entity_pair is not None:
            return self._get_local_remote_snapshots(entity_pair, 'volumes' if result['entity_type'] != 'FILESYSTEM' else 'filesystems', remote_replica, '_{0}_reclaimed_snapshot_id')
        return None, None

    def _get_local_remote_snapshots(self, result, collection_name, remote_replica, field_name_template):
        local_reclaimed_id = result.get(field_name_template.format('local'))
        if local_reclaimed_id is None:
            _logger.debug('Could not get local reclaimed id (missing {0} in {1})', field_name_template.format('local'), result)
        remote_reclaimed_id = result.get(field_name_template.format('remote'))
        if remote_reclaimed_id is None:
            _logger.debug('Could not get remote reclaimed id (missing {0} in {1})', field_name_template.format('remote'), result)

        local = remote = None

        if local_reclaimed_id is not None:
            local = getattr(self.system, collection_name).get_by_id_lazy(local_reclaimed_id)
        if remote_replica is not None and remote_reclaimed_id is not None:
            remote = getattr(remote_replica.system, collection_name).get_by_id_lazy(remote_reclaimed_id)
        return local, remote


    def get_remote_replica(self, from_cache=False):
        """Get the corresponsing replica object in the remote machine. For this to work, the SDK user should
        call the register_related_system method of the Infinibox object when a link to a remote system is consructed
        for the first time"""
        linked_system = self.get_link(from_cache=from_cache).get_linked_system()
        if linked_system is None:
            return None
        return linked_system.replicas.get_by_id_lazy(self.get_remote_replica_id(from_cache=from_cache))

    def get_remote_entity(self):
        """Fetches the remote replicated entity if available
        """
        peer = self.get_remote_replica()
        if peer is None:
            return None
        return peer.get_local_entity()

    def get_remote_entity_pairs(self):
        """Returns the entity_pairs configuration as held by the remote replica

        .. note:: this uses the remote command execution API to run the command over the inter-system
          link
        """
        return self.system.api.get('remote/{0}/api/rest/replicas/{1}'.format(
            self.get_link().id,
            self.get_remote_replica_id(from_cache=True))).get_result()['entity_pairs']
