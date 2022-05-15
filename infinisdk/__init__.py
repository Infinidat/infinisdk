from .core.q import Q  # pylint: disable=unused-import

from .infinibox import InfiniBox
from .infinibox.components import InfiniBoxSystemComponents

_SDK_HOOK = 'infinidat.sdk.{}'.format


def _get_system_tag_names(system_cls, sdk_classes):
    return set(tag for obj_cls in sdk_classes for tag in obj_cls.get_tags_for_object_operations(system_cls))

def _install_hooks():
    import gossip

    # Define systems objects operation hooks.
    obj_type_names = _get_system_tag_names(InfiniBox, InfiniBox.OBJECT_TYPES + InfiniBox.SUB_OBJECT_TYPES)
    obj_type_names.add('event')

    component_type_names = _get_system_tag_names(InfiniBox, InfiniBoxSystemComponents.types.to_list())
    # Update is the only action which components can perform (it cannot be created or deleted)
    update_tag_names = obj_type_names | component_type_names


    # pylint: disable=too-many-format-args
    gossip.define(_SDK_HOOK('pre_object_creation'), tags=obj_type_names, arg_names=('data', 'system', 'cls', 'parent'))
    gossip.define(_SDK_HOOK('post_object_creation'), tags=obj_type_names,
                  arg_names=('obj', 'data', 'response_dict', 'parent'))
    gossip.define(_SDK_HOOK('object_creation_failure'), tags=obj_type_names,
                  arg_names=('data', 'system', 'cls', 'parent', 'exception'))

    gossip.define(_SDK_HOOK('pre_object_deletion'), tags=obj_type_names, arg_names=('obj', 'url'))
    gossip.define(_SDK_HOOK('post_object_deletion'), tags=obj_type_names, arg_names=('obj', 'url'))
    gossip.define(_SDK_HOOK('object_deletion_failure'), tags=obj_type_names,
                  arg_names=('obj', 'exception', 'system', 'url'))

    gossip.define(_SDK_HOOK('pre_object_update'), tags=update_tag_names, arg_names=('obj', 'data'))
    gossip.define(_SDK_HOOK('post_object_update'), tags=update_tag_names, arg_names=('obj', 'data', 'response_dict'))
    gossip.define(_SDK_HOOK('object_update_failure'), tags=update_tag_names,
                  arg_names=('obj', 'exception', 'system', 'data'))

    gossip.define(_SDK_HOOK('object_operation_failure'), tags=update_tag_names, arg_names=('exception',))

    gossip.define(_SDK_HOOK('pre_treeq_creation'), tags=['infinibox', 'treeq'],
                  arg_names=('fields', 'system', 'filesystem'))
    gossip.define(_SDK_HOOK('post_treeq_creation'), tags=['infinibox', 'treeq'],
                  arg_names=('fields', 'system', 'filesystem', 'treeq'))
    gossip.define(_SDK_HOOK('treeq_creation_failure'), tags=['infinibox', 'treeq'],
                  arg_names=('fields', 'system', 'filesystem', 'exception'))

    gossip.define(_SDK_HOOK("begin_fork"), tags=['infinibox', 'volume', 'filesystem'], arg_names=('obj',))
    gossip.define(_SDK_HOOK("cancel_fork"), tags=['infinibox', 'volume', 'filesystem'], arg_names=('obj',))
    gossip.define(_SDK_HOOK("finish_fork"), tags=['infinibox', 'volume', 'filesystem'], arg_names=('obj', 'child'))

    gossip.define(_SDK_HOOK('pre_data_restore'), tags=['infinibox', 'volume', 'filesystem'],
                  arg_names=('source', 'target'))
    gossip.define(_SDK_HOOK('post_data_restore'), tags=['infinibox', 'volume', 'filesystem'],
                  arg_names=('source', 'target', 'require_real_data', 'reason'))
    gossip.define(_SDK_HOOK('data_restore_failure'), tags=['infinibox', 'volume', 'filesystem'],
                  arg_names=('source', 'target', 'exc'))

    gossip.define(_SDK_HOOK('pre_object_restore'), tags=['infinibox', 'volume', 'filesystem'],
                  arg_names=('source', 'target'))
    gossip.define(_SDK_HOOK('post_object_restore'), tags=['infinibox', 'volume', 'filesystem'],
                  arg_names=('source', 'target'))
    gossip.define(_SDK_HOOK('object_restore_failure'), tags=['infinibox', 'volume', 'filesystem'],
                  arg_names=('source', 'target', 'exc'))

    gossip.define(_SDK_HOOK('pre_pool_move'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('obj', 'with_capacity', 'system', 'target_pool', 'source_pool'))
    gossip.define(_SDK_HOOK('post_pool_move'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('obj', 'with_capacity', 'system', 'target_pool', 'source_pool'))
    gossip.define(_SDK_HOOK('pool_move_failure'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('obj', 'with_capacity', 'system', 'exception', 'target_pool', 'source_pool'))


    gossip.define(_SDK_HOOK('pre_cons_group_deletion'), tags=['infinibox', 'cons_group'],
                  arg_names=('cons_group', 'delete_members'))
    gossip.define(_SDK_HOOK('post_cons_group_deletion'), tags=['infinibox', 'cons_group'],
                  arg_names=('cons_group', 'delete_members'))
    gossip.define(_SDK_HOOK('cons_group_deletion_failure'), tags=['infinibox', 'cons_group'],
                  arg_names=('cons_group', 'delete_members'))

    gossip.define(_SDK_HOOK('pre_entity_child_creation'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('source', 'system'))
    gossip.define(_SDK_HOOK('post_entity_child_creation'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('source', 'target', 'system'))
    gossip.define(_SDK_HOOK('entity_child_creation_failure'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('obj', 'exception', 'system'))

    gossip.define(_SDK_HOOK('pre_creation_data_validation'), tags=obj_type_names, arg_names=('fields', 'system', 'cls'))

    gossip.define(_SDK_HOOK('pre_fields_update'), tags=update_tag_names, arg_names=('fields', 'source'))

    gossip.define(_SDK_HOOK('pre_cons_group_add_member'), tags=['infinibox'],
                  arg_names=('cons_group', 'member', 'request'))
    gossip.define(_SDK_HOOK('post_cons_group_add_member'), tags=['infinibox'],
                  arg_names=('cons_group', 'member', 'request'))
    gossip.define(_SDK_HOOK('cons_group_add_member_failure'), tags=['infinibox'],
                  arg_names=('cons_group', 'member', 'request'))

    gossip.define(_SDK_HOOK('pre_cons_group_remove_member'), tags=['infinibox'],
                  arg_names=('cons_group', 'member'))
    gossip.define(_SDK_HOOK('post_cons_group_remove_member'), tags=['infinibox'],
                  arg_names=('cons_group', 'member'))
    gossip.define(_SDK_HOOK('cons_group_remove_member_failure'), tags=['infinibox'],
                  arg_names=('cons_group', 'member'))

    gossip.define(_SDK_HOOK('replica_snapshot_created'), tags=['infinibox'],
                  arg_names=('snapshot', 'replica_deleted', 'replica_exposed'))
    gossip.define(_SDK_HOOK('replica_deleted'), tags=['infinibox'], arg_names=('replica', 'entity_pairs',\
                                                                               'deletion_params'))

    gossip.define(_SDK_HOOK('pre_replication_snapshot_expose'), tags=['volume', 'filesystem', 'cons_group'])
    gossip.define(_SDK_HOOK('post_replication_snapshot_expose'), tags=['volume', 'filesystem', 'cons_group'])
    gossip.define(_SDK_HOOK('replication_snapshot_expose_failure'), tags=['volume', 'filesystem', 'cons_group'])

    gossip.define(_SDK_HOOK('pre_replica_suspend'), tags=['infinibox'], arg_names=('replica',))
    gossip.define(_SDK_HOOK('post_replica_suspend'), tags=['infinibox'], arg_names=('replica',))
    gossip.define(_SDK_HOOK('replica_suspend_failure'), tags=['infinibox'], arg_names=('replica', 'exception'))

    gossip.define(_SDK_HOOK('pre_replica_resume'), tags=['infinibox'], arg_names=('replica',))
    gossip.define(_SDK_HOOK('post_replica_resume'), tags=['infinibox'], arg_names=('replica',))
    gossip.define(_SDK_HOOK('replica_resume_failure'), tags=['infinibox'], arg_names=('replica', 'exception'))

    gossip.define(_SDK_HOOK('pre_replica_change_type'), tags=['infinibox'],
                  arg_names=('replica', 'old_type', 'new_type'))
    gossip.define(_SDK_HOOK('post_replica_change_type'), tags=['infinibox'],
                  arg_names=('replica', 'old_type', 'new_type'))
    gossip.define(_SDK_HOOK('replica_change_type_failure'), tags=['infinibox'],
                  arg_names=('replica', 'old_type', 'new_type', 'exception'))

    gossip.define(_SDK_HOOK('pre_replica_switch_role'), tags=['infinibox'], arg_names=('replica',))
    gossip.define(_SDK_HOOK('post_replica_switch_role'), tags=['infinibox'], arg_names=('replica',))
    gossip.define(_SDK_HOOK('replica_switch_role_failure'), tags=['infinibox'], arg_names=('replica', 'exception'))

    gossip.define(_SDK_HOOK('pre_replica_change_role'), tags=['infinibox'], arg_names=('replica',))
    gossip.define(_SDK_HOOK('post_replica_change_role'), tags=['infinibox'], arg_names=('replica',))
    gossip.define(_SDK_HOOK('replica_change_role_failure'), tags=['infinibox'], arg_names=('replica', 'exception'))

    gossip.define(_SDK_HOOK('pre_refresh_snapshot'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('source', 'target'))
    gossip.define(_SDK_HOOK('post_refresh_snapshot'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('source', 'target'))
    gossip.define(_SDK_HOOK('refresh_snapshot_failure'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'],
                  arg_names=('source', 'target'))

    gossip.define(_SDK_HOOK('pre_pool_lock'), tags=['infinibox', 'pool'], arg_names=('pool',))
    gossip.define(_SDK_HOOK('post_pool_lock'), tags=['infinibox', 'pool'], arg_names=('pool',))
    gossip.define(_SDK_HOOK('pool_lock_failure'), tags=['infinibox', 'pool'], arg_names=('pool', 'exception'))

    gossip.define(_SDK_HOOK('pre_pool_unlock'), tags=['infinibox', 'pool'], arg_names=('pool',))
    gossip.define(_SDK_HOOK('post_pool_unlock'), tags=['infinibox', 'pool'], arg_names=('pool',))
    gossip.define(_SDK_HOOK('pool_unlock_failure'), tags=['infinibox', 'pool'], arg_names=('pool', 'exception'))

    gossip.define(_SDK_HOOK('pre_cluster_add_host'), tags=['infinibox', 'host_cluster'],
                  arg_names=('host', 'cluster'))
    gossip.define(_SDK_HOOK('post_cluster_add_host'), tags=['infinibox', 'host_cluster'],
                  arg_names=('host', 'cluster'))
    gossip.define(_SDK_HOOK('cluster_add_host_failure'), tags=['infinibox', 'host_cluster'],
                  arg_names=('host', 'cluster', 'exception'))

    gossip.define(_SDK_HOOK('pre_cluster_remove_host'), tags=['infinibox', 'host_cluster'],
                  arg_names=('host', 'cluster'))
    gossip.define(_SDK_HOOK('post_cluster_remove_host'), tags=['infinibox', 'host_cluster'],
                  arg_names=('host', 'cluster'))
    gossip.define(_SDK_HOOK('cluster_remove_host_failure'), tags=['infinibox', 'host_cluster'],
                  arg_names=('host', 'cluster', 'exception'))

    gossip.define(_SDK_HOOK('pre_qos_policy_assign'), tags=['infinibox', 'qos_policy'],
                  arg_names=('qos_policy', 'entity'))
    gossip.define(_SDK_HOOK('post_qos_policy_assign'), tags=['infinibox', 'qos_policy'],
                  arg_names=('qos_policy', 'entity'))
    gossip.define(_SDK_HOOK('qos_policy_assign_failure'), tags=['infinibox', 'qos_policy'],
                  arg_names=('qos_policy', 'entity', 'exception'))

    gossip.define(_SDK_HOOK('pre_qos_policy_unassign'), tags=['infinibox', 'qos_policy'],
                  arg_names=('qos_policy', 'entity'))
    gossip.define(_SDK_HOOK('post_qos_policy_unassign'), tags=['infinibox', 'qos_policy'],
                  arg_names=('qos_policy', 'entity'))
    gossip.define(_SDK_HOOK('qos_policy_unassign_failure'), tags=['infinibox', 'qos_policy'],
                  arg_names=('qos_policy', 'entity', 'exception'))

    gossip.define(_SDK_HOOK('before_api_request'), arg_names=('request',))
    gossip.define(_SDK_HOOK('after_api_request'), arg_names=('request', 'response'))

    gossip.define(_SDK_HOOK('after_login'), arg_names=('system',))

    gossip.define(_SDK_HOOK('pre_volume_mapping'),
                  arg_names=('volume', 'host_or_cluster', 'lun'), tags=['infinibox', 'host', 'host_cluster'])
    gossip.define(_SDK_HOOK('post_volume_mapping'),
                  arg_names=('volume', 'host_or_cluster', 'lun', 'lun_object'),
                  tags=['infinibox', 'host', 'host_cluster'])
    gossip.define(_SDK_HOOK('volume_mapping_failure'),
                  arg_names=('volume', 'host_or_cluster', 'exception', 'lun'),
                  tags=['infinibox', 'host', 'host_cluster'])
    gossip.define(_SDK_HOOK('pre_volume_unmapping'),
                  arg_names=('volume', 'host_or_cluster', 'lun'), tags=['infinibox', 'host', 'host_cluster'])
    gossip.define(_SDK_HOOK('post_volume_unmapping'),
                  arg_names=('volume', 'host_or_cluster', 'lun'), tags=['infinibox', 'host', 'host_cluster'])
    gossip.define(_SDK_HOOK('volume_unmapping_failure'),
                  arg_names=('volume', 'host_or_cluster', 'exception', 'lun'),
                  tags=['infinibox', 'host', 'host_cluster'])

    gossip.define(_SDK_HOOK('pre_event_retention'), tags=['infinibox', 'event'], arg_names=('system', 'retention'))
    gossip.define(_SDK_HOOK('post_event_retention'), tags=['infinibox', 'event'], arg_names=('system', 'retention'))
    gossip.define(_SDK_HOOK('event_retention_failure'), tags=['infinibox', 'event'],
                  arg_names=('system', 'retention', 'exception'))

    gossip.define(_SDK_HOOK('witness_address_set'), tags=['infinibox'], arg_names=('witness_address',))

    gossip.define(_SDK_HOOK('pre_replication_group_remove_member'), tags=['infinibox'],
                  arg_names=('replication_group', 'member'))
    gossip.define(_SDK_HOOK('post_replication_group_remove_member'), tags=['infinibox'],
                  arg_names=('replication_group', 'member'))
    gossip.define(_SDK_HOOK('replication_group_remove_member_failure'), tags=['infinibox'],
                  arg_names=('replication_group', 'member'))

    gossip.define(_SDK_HOOK('pre_rg_replica_suspend'), tags=['infinibox'], arg_names=('rg_replica',))
    gossip.define(_SDK_HOOK('post_rg_replica_suspend'), tags=['infinibox'], arg_names=('rg_replica',))
    gossip.define(_SDK_HOOK('rg_replica_suspend_failure'), tags=['infinibox'], arg_names=('rg_replica', 'exception'))

    gossip.define(_SDK_HOOK('pre_rg_replica_resume'), tags=['infinibox'], arg_names=('rg_replica',))
    gossip.define(_SDK_HOOK('post_rg_replica_resume'), tags=['infinibox'], arg_names=('rg_replica',))
    gossip.define(_SDK_HOOK('rg_replica_resume_failure'), tags=['infinibox'], arg_names=('rg_replica', 'exception'))

    gossip.get_or_create_group('infinidat.sdk').set_strict()

_install_hooks()
