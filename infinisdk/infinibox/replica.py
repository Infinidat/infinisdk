###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from contextlib import contextmanager
from datetime import timedelta
import requests

import gossip

from ..core.api.special_values import Autogenerate, OMIT
from ..core.type_binder import TypeBinder
from ..core import Field
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import TooManyObjectsFound, CannotGetReplicaState, APICommandFailed, InfiniSDKRuntimeException
from ..core.translators_and_types import MillisecondsDeltaType
from .system_object import InfiniBoxObject


class ReplicaBinder(TypeBinder):

    """Implements *system.replicas*
    """
    def replicate_volume(self, volume, remote_volume=None, **kw):
        """Convenience wrapper around :func:`.replicate_entity`
        """
        return self.replicate_entity(entity=volume, remote_entity=remote_volume, **kw)

    def replicate_cons_group(self, cg, remote_cg=None, **kw):
        """Convenience wrapper around :func:`.replicate_entity`
        """
        return self.replicate_entity(entity=cg, remote_entity=remote_cg, **kw)


    def replicate_entity(self, entity, link, remote_pool=None, remote_entity=None, **kw):
        """Replicates a entity or CG, creating its remote replica on the specified pool

        :param remote_pool: if omitted, ``remote_entity`` must be specified. Otherwise, means creating target entity
        :param remote_entity: if omitted, ``remote_pool`` must be specified. Otherwise, means creating based on existing entity on target
        """
        if remote_entity is None:
            assert remote_pool is not None
            return self.replicate_entity_create_target(entity, link, remote_pool=remote_pool, **kw)
        return self.replicate_entity_existing_target(entity, link, remote_entity=remote_entity, **kw)

    def replicate_entity_create_target(self, entity, link, remote_pool, **kw):
        return self._replicate(entity, link, base_action='CREATE', remote_pool_id=remote_pool.id, **kw)

    def replicate_entity_existing_target(self, entity, link, remote_entity=None, **kw):
        return self._replicate(entity, link, remote_entity=remote_entity, base_action='NO_BASE_DATA', **kw)

    def _replicate(self, entity, link, base_action, remote_entity=None, **kw):

        kw['link'] = link
        kw['entity_pairs'] = []
        entity_pairs = []
        if isinstance(entity, entity.system.cons_groups.object_type):
            kw['entity_type'] = 'CONSISTENCY_GROUP'
            kw['local_cg_id'] = entity.id
            if remote_entity is not None:
                kw['remote_cg_id'] = remote_entity.id

            for member in entity.get_members():
                if remote_entity is not None:
                    raise NotImplementedError("Replicating a non-empty CG to an existing CG is not supported in InfiniSDK at the moment") # pragma: no cover
                entity_pairs.append((member, None))
        else:
            kw['entity_type'] = 'VOLUME'
            entity_pairs.append((entity, remote_entity))


        for local, remote in entity_pairs:
            kw['entity_pairs'].append({
                'local_entity_id': local.id,
                'remote_entity_id': remote.id if remote else None,
                'remote_base_action': base_action,
            })

        return self.create(**kw)

    def _get_entity_type_string(self, entity):
        if isinstance(entity, entity.system.cons_groups.object_type):
            return 'CONSISTENCY_GROUP'
        return 'VOLUME'


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
        Field('role', type=str),
        Field('progress', type=int),
        Field('last_synchronized', type=int),
        Field('state', type=str),
        Field('sync_interval', api_name='sync_interval', type=MillisecondsDeltaType,
              mutable=True,
              creation_parameter=True, default=timedelta(seconds=30)),

        Field('rpo', api_name='rpo_value', type=MillisecondsDeltaType, mutable=True),

    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_replication()

    def _get_entity_collection(self):
        if self.get_entity_type(from_cache=True) == 'VOLUME':
            return self.system.volumes
        return self.system.cons_groups

    def get_local_entity(self):
        """Returns the local entity used for replication, be it a volume or a consistency group.
        """
        if self.is_consistency_group():
            return self.system.cons_groups.get_by_id_lazy(self.get_field('local_cg_id', from_cache=True))

        pairs = self.get_entity_pairs(from_cache=True)
        if len(pairs) > 1:
            raise TooManyObjectsFound()
        [pair] = pairs
        return self.system.volumes.get_by_id_lazy(pair['local_entity_id'])

    def expose_last_consistent_snapshot(self):
        resp = self.system.api.post(self.get_this_url_path().add_path('expose_last_consistent_snapshot')).get_result()
        if self.is_consistency_group():
            snapshot_id = resp['_local_reclaimed_sg_id']
        else:
            snapshot_id = resp['entity_pairs'][0]['_local_reclaimed_snapshot_id']
        if snapshot_id is None:
            return None
        return self._get_entity_collection().get_by_id_lazy(snapshot_id)

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
            return self.get_local_entity().get_members()
        return [self.get_local_entity()]

    def is_consistency_group(self):
        """Returns whether this replica is configured with a consistency group as a local entity
        """
        return self.get_field('entity_type', from_cache=True).lower() == 'consistency_group'

    def suspend(self):
        """Suspends this replica
        """
        self.system.api.post(self.get_this_url_path().add_path('suspend'))
        self.refresh('state')

    def sync(self):
        """Starts a sync job
        """
        returned = self.system.api.post(self.get_this_url_path().add_path('sync'), headers={'X-INFINIDAT-RAW-RESPONSE': 'true'})
        return returned.get_result()

    def resume(self):
        """Resumes this replica
        """
        self.system.api.post(self.get_this_url_path().add_path('resume'))
        self.refresh('state')

    def _validate_can_check_state(self):
        if self.is_target():
            raise CannotGetReplicaState('Replica state cannot be checked on target replica')

    def is_suspended(self, *args, **kwargs):
        """Returns whether or not this replica is in suspended state
        """
        self._validate_can_check_state()
        return self.get_state(*args, **kwargs).lower() == 'suspended'

    def is_idle(self, *args, **kwargs):
        """Returns whether or not this replica is in idle state
        """
        self._validate_can_check_state()
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
        return 'initial' in self.get_state(*args, **kwargs).lower()

    def is_replicating(self, *args, **kwargs):
        """Returns whether or not this replica is in replicating state
        """
        self._validate_can_check_state()
        return self.get_state(*args, **kwargs).lower() == 'replicating'

    def is_active(self, *args, **kwargs):
        self._validate_can_check_state()
        return self.get_state(*args, **kwargs).lower() in ['idle', 'initiating', 'replicating']

    def change_role(self, entity_pairs=OMIT):
        data = {'entity_pairs': entity_pairs} if entity_pairs is not OMIT else None
        self.system.api.post(self.get_this_url_path()
                                 .add_path('change_role'), data=data)
        self.refresh()
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

    def delete(self, retain_staging_area=False, force_if_remote_error=False, force_on_target=False, force_if_no_remote_credentials=False):
        returned = set()

        path = self.get_this_url_path()
        if retain_staging_area:
            path = path.add_query_param('retain_staging_area', 'true')
        if force_if_remote_error:
            path = path.add_query_param('force_if_remote_error', 'true')
        if force_on_target:
            path = path.add_query_param('force_on_target', 'true')
        if force_if_no_remote_credentials:
            path = path.add_query_param('force_if_no_remote_credentials', 'true')

        with self._detecting_new_snapshots_context(retain_staging_area, returned):
            with self._get_delete_context():
                self.system.api.delete(path)

        return returned

    @contextmanager
    def _detecting_new_snapshots_context(self, retain_staging_area, result_set):
        if not retain_staging_area:
            yield
            return

        entities = [self.get_local_volume()]
        remote_replica = self.get_remote_replica()
        if remote_replica is not None:
            try:
                entities.append(remote_replica.get_local_volume())
            except APICommandFailed as e:
                if e.response.status_code != requests.codes.not_found:
                    raise
                entities = []

        old_snaps = set(child for entity in entities for child in entity.get_children())
        yield
        new_snaps = set(child for entity in entities for child in entity.get_children()) - old_snaps

        for snap in new_snaps:
            gossip.trigger_with_tags('infinidat.sdk.replica_snapshot_created', {'snapshot': snap}, tags=['infinibox'])

        result_set.update(new_snaps)

    def get_remote_replica(self, from_cache=False):
        """Get the corresponsing replica object in the remote machine. For this to work, the SDK user should
        call the register_related_system method of the Infinibox object when a link to a remote system is consructed
        for the first time"""
        linked_system = self.get_link(from_cache=from_cache).get_linked_system()
        return linked_system.replicas.get_by_id_lazy(self.get_remote_replica_id(from_cache=from_cache))

    def get_remote_entity_pairs(self):
        """Returns the entity_pairs configuration as held by the remote replica

        .. note:: this uses the remote command execution API to run the command over the inter-system
          link
        """
        return self.system.api.get('remote/{0}/api/rest/replicas/{1}'.format(
            self.get_link().id,
            self.get_remote_replica_id(from_cache=True))).get_result()['entity_pairs']
