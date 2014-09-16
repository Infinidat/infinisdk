###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from .core.q import Q

from .infinibox import InfiniBox
from .izbox import IZBox


def _install_hooks():
    import gossip

    # Define systems objects operation hooks
    obj_type_name = set(tag for sys in (InfiniBox, IZBox) for obj_cls in sys.OBJECT_TYPES
            for tag in obj_cls._get_tags_for_object_operations(sys))
    for hook_name_template in ('infinidat.sdk.pre_object_{0}', 'infinidat.sdk.post_object_{0}'):
        for operation in ('creation', 'deletion'):
            full_hook_name = hook_name_template.format(operation)
            gossip.define(full_hook_name, tags=obj_type_name)
    gossip.define('infinidat.sdk.object_operation_failure', tags=obj_type_name)

    gossip.define("infinidat.sdk.begin_fork",  tags=['infinibox', 'volume', 'filesystem'])
    gossip.define("infinidat.sdk.cancel_fork", tags=['infinibox', 'volume', 'filesystem'])
    gossip.define("infinidat.sdk.finish_fork", tags=['infinibox', 'volume', 'filesystem'])

    gossip.define('infinidat.sdk.pre_data_restore', tags=['infinibox', 'volume', 'filesystem'])
    gossip.define('infinidat.sdk.post_data_restore', tags=['infinibox', 'volume', 'filesystem'])
    gossip.define('infinidat.sdk.data_restore_failure', tags=['infinibox', 'volume', 'filesystem'])

    gossip.define('infinidat.sdk.pre_node_phase_in', tags=['infinibox', 'node1', 'node2', 'node3'])
    gossip.define('infinidat.sdk.post_node_phase_in', tags=['infinibox', 'node1', 'node2', 'node3'])
    gossip.define('infinidat.sdk.node_phase_in_failure', tags=['infinibox', 'node1', 'node2', 'node3'])

    gossip.define('infinidat.sdk.pre_node_phase_out', tags=['infinibox', 'node1', 'node2', 'node3'])
    gossip.define('infinidat.sdk.post_node_phase_out', tags=['infinibox', 'node1', 'node2', 'node3'])
    gossip.define('infinidat.sdk.node_phase_out_failure', tags=['infinibox', 'node1', 'node2', 'node3'])

    gossip.get_or_create_group('infinidat.sdk').set_strict()



_install_hooks()
