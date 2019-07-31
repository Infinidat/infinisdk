import gossip

def handle_possible_replication_snapshot(snapshot):
    fields = snapshot.get_fields(from_cache=True, raw_value=True)
    if fields.get('rmr_snapshot_guid', None) or fields.get('data_snapshot_guid', None):
        gossip.trigger_with_tags('infinidat.sdk.replica_snapshot_created',
                                 {'snapshot': snapshot, 'replica_deleted': False},
                                 tags=['infinibox'])
