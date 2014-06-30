from infinisdk import Q


def test_query_with_q(infinibox, volume):
    [v] = infinibox.volumes.find(Q.size >= volume.get_size())
    assert v == volume
