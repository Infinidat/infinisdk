import gossip
import functools

from collections import namedtuple
from ..core import Field, MillisecondsDatetimeType
from ..core.api.special_values import OMIT
from ..core.object_query import PolymorphicQuery
from ..core.bindings import RelatedObjectBinding
from ..core.api.special_values import Autogenerate
from ..core.utils import end_reraise_context, handle_possible_replication_snapshot
from .system_object import InfiniBoxObject

_CG_SUFFIX = Autogenerate('_{timestamp}')


class ConsGroup(InfiniBoxObject):
    URL_PATH = 'cgs'
    ENTITY_TYPES = namedtuple('VolumeTypes', ['Master', 'Snapshot'])('MASTER', 'SNAPSHOT')

    FIELDS = [
        Field("id", is_identity=True, type=int, cached=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("cg_{uuid}")),
        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("pool", type='infinisdk.infinibox.pool:Pool', api_name="pool_id", creation_parameter=True,
              is_filterable=True, is_sortable=True, binding=RelatedObjectBinding()),
        Field("parent", type='infinisdk.infinibox.cons_group:ConsGroup', cached=True, api_name="parent_id",
              binding=RelatedObjectBinding('cons_groups'), is_filterable=True, is_sortable=True),
        Field("replicated", api_name="is_replicated", type=bool, is_filterable=True, is_sortable=True),
        Field("members_count", type=int, is_filterable=True, is_sortable=True),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field('rmr_snapshot_guid', is_filterable=True, is_sortable=True),
        Field('pool_name', is_sortable=True, is_filterable=True, new_to="4.0.10"),
        Field("lock_expires_at", type=MillisecondsDatetimeType, creation_parameter=True, optional=True,
              mutable=True, feature_name='snapshot_lock'),
        Field("lock_state", type=str, feature_name='snapshot_lock'),
        Field("tenant", api_name="tenant_id", binding=RelatedObjectBinding('tenants'),
              type='infinisdk.infinibox.tenant:Tenant', feature_name='tenants', is_filterable=True, is_sortable=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_consistency_groups()

    @classmethod
    def get_type_name(cls):
        return 'cons_group'

    def is_master(self):
        return self.get_type() == self.ENTITY_TYPES.Master

    def _get_snapshot_type(self):
        return 'SNAPSHOT' if self.system.compat.has_writable_snapshots() else 'SNAP'

    def is_snapgroup(self):
        """Checks if this is a snapshot group (as opposed to consistency group)
        """
        return self.get_type() == self._get_snapshot_type()

    def get_children(self):
        return self.find(self.system, parent=self)

    def get_replicas(self):
        return self.system.replicas.find(local_cg_id=self.id)

    get_snapgroups = get_children

    def create_snapgroup(self, name=None, prefix=None, suffix=None, lock_expires_at=None):
        """Create a snapshot group out of the consistency group.
        """
        hook_tags = self.get_tags_for_object_operations(self)
        gossip.trigger_with_tags('infinidat.sdk.pre_entity_child_creation',
                                 {'source': self, 'system': self.system},
                                 tags=hook_tags)

        self.invalidate_cache('members_count')
        if not name:
            name = self.fields.name.generate_default().generate()
        if not prefix and not suffix:
            suffix = _CG_SUFFIX.generate()
        data = {'snap_prefix': prefix, 'parent_id': self.get_id(), 'snap_suffix': suffix, 'name': name}
        if self.system.compat.has_snapshot_lock():
            for key, val in [('lock_expires_at', lock_expires_at)]:
                data[key] = self.fields.get(key).binding.get_api_value_from_value(self.system, type(self), None, val)
        members = self.get_members()
        for member in members:
            member.trigger_begin_fork()
        try:
            child = self._create(self.system, self.get_url_path(self.system), data=data, tags=None)
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                gossip.trigger_with_tags('infinidat.sdk.entity_child_failure',
                                         {'obj': self, 'exception': e, 'system': self.system},
                                         tags=hook_tags)
                for member in members:
                    member.trigger_cancel_fork()
        child_members = dict((snapshot.get_parent(from_cache=True).id, snapshot) for snapshot in child.get_members())
        for member in members:
            snap = child_members[member.id]
            member.trigger_finish_fork(snap)
            handle_possible_replication_snapshot(snap)

        gossip.trigger_with_tags('infinidat.sdk.post_entity_child_creation',
                                 {'source': self, 'target': child, 'system': self.system},
                                 tags=hook_tags)
        return child

    create_snapshot = create_snapgroup

    def refresh_snapgroup(self):
        """Refresh a snapshot group with the most recent data from the parent consistency group
        """
        parent = self.get_parent()

        sg_members_by_parent_id = dict((s.get_field('parent_id', from_cache=True), s) for s in self.get_members())
        cg_members_by_id = dict((m.id, m) for m in parent.get_members() if m.id in sg_members_by_parent_id)

        began_fork = []
        trigger_hook = functools.partial(gossip.trigger_with_tags,
                                         kwargs={'source': parent, 'target': self},
                                         tags=self.get_tags_for_object_operations(self.system))

        trigger_hook('infinidat.sdk.pre_refresh_snapshot')
        try:
            for member in cg_members_by_id.values():
                member.trigger_begin_fork()
                began_fork.append(member)
            self.system.api.post(self.get_this_url_path().add_path('refresh'), data={'source_id': parent.id})
        except Exception:  # pylint: disable=broad-except
            with end_reraise_context():
                for member in began_fork:
                    member.trigger_cancel_fork()
                trigger_hook('infinidat.sdk.refresh_snapshot_failure')
        for member in cg_members_by_id.values():
            member.trigger_finish_fork(sg_members_by_parent_id[member.id])
        trigger_hook('infinidat.sdk.post_refresh_snapshot')

    refresh_snapshot = refresh_snapgroup

    def delete(self, delete_members=OMIT, force_if_snapshot_locked=OMIT):  # pylint: disable=arguments-differ
        """Deletes the consistency group

        :param delete_members: if True, deletes the member datasets as well as the group itself
        """
        trigger_hook = functools.partial(gossip.trigger_with_tags,
                                         kwargs={'cons_group': self, 'delete_members': delete_members},
                                         tags=self.get_tags_for_object_operations(self.system))
        trigger_hook('infinidat.sdk.pre_cons_group_deletion')

        try:
            self._send_delete_with_hooks_tirggering(self.get_this_url_path(),
                                                    delete_members=delete_members,
                                                    force_if_snapshot_locked=force_if_snapshot_locked)
        except Exception:  # pylint: disable=broad-except
            with end_reraise_context():
                trigger_hook('infinidat.sdk.cons_group_deletion_failure')

        trigger_hook('infinidat.sdk.post_cons_group_deletion')

    def _get_members_url(self):
        return self.get_this_url_path().add_path('members')

    def get_members(self, **kwargs):
        """
        Retrieves a lazy query for the consistency group's member datasets

        .. note:: in many cases you should prefer to collect the result of this method as a list using ``to_list()``:
           .. code-block:: python

              member_list = cg.get_members().to_list()

        :param kwargs: Optional parameter containing filterable fields of cg member for filtering the members returned
        """
        def object_factory(system, received_item):
            type_name = 'volume' if received_item['dataset_type'] == 'VOLUME' else 'filesystem'
            return system.objects.get_binder_by_type_name(type_name).object_type.construct(system, received_item)

        object_types = (self.system.volumes.object_type, self.system.filesystems.object_type)
        ret = PolymorphicQuery(self.system, self._get_members_url(), object_types, object_factory)
        if kwargs:
            ret.extend_url(**kwargs)
        return ret

    def add_member(self, member, **kwargs):
        """Adds a member data entity to this consistency group

        :param remote_entity: Assuming this CG is currently being replicated, specifies the remote entity for
           the member replication
        """
        data = kwargs
        data['dataset_id'] = member.id
        remote_entity = kwargs.pop('remote_entity', None)
        if remote_entity is not None:
            data['replication_pair_info'] = {
                'remote_base_action': 'NO_BASE_DATA',
                'remote_entity_id': remote_entity.id
            }
        trigger_hook = functools.partial(gossip.trigger_with_tags,
                                         kwargs={'cons_group': self, 'member': member, 'request': data},
                                         tags=['infinibox'])
        trigger_hook('infinidat.sdk.pre_cons_group_add_member')
        try:
            self.system.api.post(self._get_members_url(), data=data)
        except Exception:  # pylint: disable=broad-except
            with end_reraise_context():
                trigger_hook('infinidat.sdk.cons_group_add_member_failure')
        trigger_hook('infinidat.sdk.post_cons_group_add_member')
        self.invalidate_cache('members_count')
        member.invalidate_cache('cons_group')

    def remove_member(self, member, retain_staging_area=False, create_replica=False, replica_name=OMIT,
                      force_if_no_remote_credentials=False, force_if_remote_error=False, force_on_target=False,
                      force_on_local=OMIT, keep_serial_on_local=OMIT):
        """Removes a volume member from this consistency group"""

        path = self._get_members_url().add_path(str(member.id))

        if retain_staging_area:
            path = path.set_query_param('retain_staging_area', 'true')
        if create_replica:
            path = path.set_query_param('create_replica', 'true')
        if force_if_no_remote_credentials:
            path = path.set_query_param('force_if_no_remote_credentials', 'true')
        if force_if_remote_error:
            path = path.set_query_param('force_if_remote_error', 'true')
        if force_on_target:
            path = path.set_query_param('force_on_target', 'true')

        if replica_name is not OMIT:
            path = path.set_query_param('replica_name', replica_name)
        if force_on_local is not OMIT:
            path = path.set_query_param('force_on_local', force_on_local)
        if keep_serial_on_local is not OMIT:
            path = path.set_query_param('keep_serial_on_local', keep_serial_on_local)

        trigger_hook = functools.partial(gossip.trigger_with_tags,
                                         kwargs={'cons_group': self, 'member': member},
                                         tags=['infinibox'])

        trigger_hook('infinidat.sdk.pre_cons_group_remove_member')
        try:
            self.system.api.delete(path)
        except Exception:  # pylint: disable=broad-except
            with end_reraise_context():
                trigger_hook('infinidat.sdk.cons_group_remove_member_failure')
        trigger_hook('infinidat.sdk.post_cons_group_remove_member')
        self.invalidate_cache('members_count')

    def restore(self, snap_group):
        """Restores this consistency group from the specified sg
        """
        sg_members_by_parent_id = dict((s.get_field('parent_id', from_cache=True), s) for s in snap_group.get_members())
        members_by_id = dict((m.id, m) for m in self.get_members() if m.id in sg_members_by_parent_id)
        for parent_id, snap in reversed(list(sg_members_by_parent_id.items())):
            members_by_id[parent_id].trigger_before_restore(snap)
        try:
            self.system.api.post(self.get_this_url_path().add_path('restore'),
                                 data={'source_id': snap_group.id})
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                for parent_id, snap in sg_members_by_parent_id.items():
                    members_by_id[parent_id].trigger_restore_failure(snap, e)
        for parent_id, snap in sg_members_by_parent_id.items():
            members_by_id[parent_id].trigger_after_restore(snap)


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
        except Exception as e:
            gossip.trigger_with_tags(
                'infinidat.sdk.pool_move_failure',
                {'obj': self, 'with_capacity': with_capacity, 'system': self.system, 'exception': e,
                 'target_pool': target_pool, 'source_pool': source_pool},
                tags=hook_tags)
            raise

        gossip.trigger_with_tags(
            'infinidat.sdk.post_pool_move',
            {'obj': self, 'with_capacity': with_capacity, 'system': self.system,
             'target_pool': target_pool, 'source_pool': source_pool},
            tags=hook_tags)

        self.invalidate_cache('pool')
