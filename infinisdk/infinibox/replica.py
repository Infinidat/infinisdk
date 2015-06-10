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
### !
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
### !
from contextlib import contextmanager
from datetime import timedelta
import requests

import gossip

from ..core.api.special_values import Autogenerate, OMIT
from ..core.type_binder import TypeBinder
from ..core import Field
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import TooManyObjectsFound, CannotGetReplicaState, APICommandFailed
from ..core.translators_and_types import MillisecondsDeltaType
from .system_object import InfiniBoxObject


class ReplicaBinder(TypeBinder):

    """Implements *system.replicas*
    """

    def replicate_volume(self, volume, link, remote_pool=None, remote_volume=None, **kw):
        """Replicates a volume, creating its remote replica on the specified pool

        :param remote_pool: if omitted, ``remote_volume`` must be specified. Otherwise, means creating target volume
        :param remote_volume: if omitted, ``remote_pool`` must be specified. Otherwise, means creating based on existing volume on target
        """
        if remote_volume is None:
            assert remote_pool is not None
            return self.replicate_volume_create_target(volume, link, remote_pool=remote_pool, **kw)
        return self.replicate_volume_existing_target(volume, link, remote_volume=remote_volume, **kw)

    def replicate_volume_create_target(self, volume, link, remote_pool, **kw):
        return self.create(
            link=link, remote_pool_id=remote_pool.id,
            entity_pairs=[{
                'local_entity_id': volume.id,
                'remote_base_action': 'CREATE',
            }], entity_type='VOLUME', **kw)

    def replicate_volume_existing_target(self, volume, link, remote_volume=None, **kw):
        return self.create(
            link=link,
            entity_pairs=[{
                'local_entity_id': volume.id,
                'remote_entity_id': remote_volume.id if remote_volume else None,
                'remote_base_action': 'NO_BASE_DATA',
            }], entity_type='VOLUME', **kw)


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

    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_replication()

    def get_local_entity(self):
        """Returns the local entity used for replication, assuming there is only one
        """
        pairs = self.get_entity_pairs(from_cache=True)
        if self.get_field('entity_type', from_cache=True).lower() != 'volume':
            raise NotImplementedError()  # pragma: no cover
        if len(pairs) > 1:
            raise TooManyObjectsFound()
        [pair] = pairs
        return self.system.volumes.get_by_id_lazy(pair['local_entity_id'])

    def get_local_volume(self):
        """Returns the local volume, assuming there is exactly one
        """
        return self.get_local_entity()

    def suspend(self):
        """Suspends this replica
        """
        self.system.api.post(self.get_this_url_path().add_path('suspend'))
        self.refresh('state')

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
