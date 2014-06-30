
def test_query_by_parent(infinibox, volume):
    snapshot = volume.create_snapshot()

    [s] = infinibox.volumes.find(parent=volume)
    assert s == snapshot

def test_query_by_parent_none(infinibox, volume):
    [v] = infinibox.volumes.find(parent=None)
    assert v == volume

def test_query_by_pool(infinibox, pool, volume):
    assert [volume] == list(infinibox.volumes.find(pool=pool))
    assert [] == list(infinibox.volumes.find(pool=None))
