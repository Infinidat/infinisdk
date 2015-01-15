###!
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
###!
import gossip
from collections import namedtuple
from ..core.exceptions import InvalidOperationException
from ..core.system_object import APICommandFailed
from .system_object import InfiniBoxObject

_BEGIN_FORK_HOOK = "infinidat.sdk.begin_fork"
_CANCEL_FORK_HOOK = "infinidat.sdk.cancel_fork"
_FINISH_FORK_HOOK = "infinidat.sdk.finish_fork"


class BaseDataEntity(InfiniBoxObject):
    PROVISIONING = namedtuple('Provisioning', ['Thick', 'Thin'])('THICK', 'THIN')
    ENTITY_TYPES = namedtuple('VolumeTypes', ['Master', 'Snapshot', 'Clone'])('MASTER', 'SNAP', 'CLONE')

    def is_master(self):
        """Returns whether or not this entity is a master entity (not a snapshot and not a clone)
        """
        return self.get_type() == self.ENTITY_TYPES.Master

    def is_snapshot(self):
        """Returns whether or not this entity is a snapshot
        """
        return self.get_type() == self.ENTITY_TYPES.Snapshot

    def is_clone(self):
        """Returns whether or not this entity is a clone
        """
        return self.get_type() == self.ENTITY_TYPES.Clone

    def _create_child(self, name):
        self.refresh('has_children')
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags(_BEGIN_FORK_HOOK, {'obj': self}, tags=hook_tags)
        if not name:
            name = self.fields.name.generate_default().generate()
        data = {'name': name, 'parent_id': self.get_id()}
        try:
            child = self._create(self.system, self.get_url_path(self.system), data=data, tags=hook_tags)
        except Exception:
            gossip.trigger_with_tags(_CANCEL_FORK_HOOK, {'obj': self}, tags=hook_tags)
            raise
        gossip.trigger_with_tags(_FINISH_FORK_HOOK, {'obj': self, 'child': child}, tags=hook_tags)
        return child

    def create_clone(self, name=None):
        """Creates a clone from this entity, if supported by the system
        """
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.pre_clone_creation', {'source': self}, tags=hook_tags)
        if self.is_snapshot():
            return self._create_child(name)
        raise InvalidOperationException('Cannot create clone for volume/clone')

    def create_snapshot(self, name=None):
        """Creates a snapshot from this entity, if supported by the system
        """
        hook_tags = self._get_tags_for_object_operations(self.system)
        gossip.trigger_with_tags('infinidat.sdk.pre_snapshot_creation', {'source': self}, tags=hook_tags)
        if self.is_snapshot():
            raise InvalidOperationException(
                'Cannot create snapshot for snapshot')
        return self._create_child(name)

    def restore(self, snapshot):
        """Restores this entity from a given snapshot object
        """
        snapshot_id = snapshot.id
        hook_tags = self._get_tags_for_object_operations(self.system)
        restore_url = self.get_this_url_path().add_path('restore')
        gossip.trigger_with_tags('infinidat.sdk.pre_data_restore', {'source': snapshot, 'target': self}, tags=hook_tags)
        try:
            self.system.api.post(restore_url, data=snapshot_id)
        except APICommandFailed as e:
            gossip.trigger_with_tags('infinidat.sdk.data_restore_failure', {'source': snapshot, 'target': self, 'exc': e}, tags=hook_tags)
            raise
        gossip.trigger_with_tags('infinidat.sdk.post_data_restore', {'source': snapshot, 'target': self}, tags=hook_tags)

    def get_snapshots(self):
        """Retrieves all snapshot children of this entity
        """
        return self.get_children(type=self.ENTITY_TYPES.Snapshot)

    def get_clones(self):
        """Retrieves all clone children of this entity
        """
        return self.get_children(type=self.ENTITY_TYPES.Clone)

    def get_children(self, **kwargs):
        """Retrieves all child entities for this entity (either clones or snapshots)
        """
        return self.find(self.system, parent_id=self.get_id(), **kwargs)

    def has_children(self):
        """Returns whether or not this entity has children
        """
        return len(self.get_children()) > 0

    def get_collection(self):
        return getattr(self.system, self.get_plural_name())

    def get_creation_time(self):
        """Retrieves creation time for this entity
        """
        return self.get_field("created_at", from_cache=True)

    @InfiniBoxObject.requires_refresh("pool")
    def move_pool(self, target_pool, with_capacity=False):
        """Moves this entity to a new pool, optionally along with its needed capacity
        """
        data = dict(pool_id=target_pool.get_id(), with_capacity=with_capacity)
        self.system.api.post(self.get_this_url_path().add_path('move'), data=data)
