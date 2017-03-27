from .core.q import Q

from .infinibox import InfiniBox

_SDK_HOOK = 'infinidat.sdk.{0}'.format

def _install_hooks():
    import gossip

    # Define systems objects operation hooks
    obj_type_name = set(tag for sys in (InfiniBox, ) for obj_cls in sys.OBJECT_TYPES
                        for tag in obj_cls.get_tags_for_object_operations(sys))
    for hook_name_template in (_SDK_HOOK('pre_object_{}'), _SDK_HOOK('post_object_{}'), _SDK_HOOK('object_{}_failure')):
        for operation in ('creation', 'deletion', 'update'):
            full_hook_name = hook_name_template.format(operation)
            gossip.define(full_hook_name, tags=obj_type_name)
    gossip.define(_SDK_HOOK('object_operation_failure'), tags=obj_type_name)

    gossip.define(_SDK_HOOK("begin_fork"), tags=['infinibox', 'volume', 'filesystem'])
    gossip.define(_SDK_HOOK("cancel_fork"), tags=['infinibox', 'volume', 'filesystem'])
    gossip.define(_SDK_HOOK("finish_fork"), tags=['infinibox', 'volume', 'filesystem'])

    gossip.define(_SDK_HOOK('pre_data_restore'), tags=['infinibox', 'volume', 'filesystem'])
    gossip.define(_SDK_HOOK('post_data_restore'), tags=['infinibox', 'volume', 'filesystem'])
    gossip.define(_SDK_HOOK('data_restore_failure'), tags=['infinibox', 'volume', 'filesystem'])

    gossip.define(_SDK_HOOK('pre_object_restore'), tags=['infinibox', 'volume', 'filesystem'])
    gossip.define(_SDK_HOOK('post_object_restore'), tags=['infinibox', 'volume', 'filesystem'])
    gossip.define(_SDK_HOOK('object_restore_failure'), tags=['infinibox', 'volume', 'filesystem'])

    gossip.define(_SDK_HOOK('pre_pool_move'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'])
    gossip.define(_SDK_HOOK('post_pool_move'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'])
    gossip.define(_SDK_HOOK('pool_move_failure'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'])

    gossip.define(_SDK_HOOK('pre_entity_child_creation'), tags=['volume', 'filesystem', 'cons_group'])
    gossip.define(_SDK_HOOK('post_entity_child_creation'), tags=['volume', 'filesystem', 'cons_group'])
    gossip.define(_SDK_HOOK('entity_child_creation_failure'), tags=['volume', 'filesystem', 'cons_group'])

    gossip.define(_SDK_HOOK('pre_creation_data_validation'), tags=obj_type_name)

    gossip.define(_SDK_HOOK('pre_fields_update'), tags=obj_type_name)

    gossip.define(_SDK_HOOK('pre_cons_group_add_member'), tags=['infinibox'])
    gossip.define(_SDK_HOOK('post_cons_group_add_member'), tags=['infinibox'])
    gossip.define(_SDK_HOOK('cons_group_add_member_failure'), tags=['infinibox'])

    gossip.define(_SDK_HOOK('pre_cons_group_remove_member'), tags=['infinibox'])
    gossip.define(_SDK_HOOK('post_cons_group_remove_member'), tags=['infinibox'])
    gossip.define(_SDK_HOOK('cons_group_remove_member_failure'), tags=['infinibox'])

    gossip.define(_SDK_HOOK('replica_snapshot_created'), tags=['infinibox'])
    gossip.define(_SDK_HOOK('replica_after_change_role'), tags=['infinibox'])

    gossip.define(_SDK_HOOK('pre_refresh_snapshot'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'])
    gossip.define(_SDK_HOOK('post_refresh_snapshot'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'])
    gossip.define(_SDK_HOOK('refresh_snapshot_failure'), tags=['infinibox', 'volume', 'filesystem', 'cons_group'])

    gossip.define(_SDK_HOOK('before_api_request'))
    gossip.define(_SDK_HOOK('after_api_request'))

    gossip.define(_SDK_HOOK('after_login'))

    gossip.get_or_create_group('infinidat.sdk').set_strict()

_install_hooks()
