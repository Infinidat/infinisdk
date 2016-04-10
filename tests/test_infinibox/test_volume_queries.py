from ..conftest import new_to_version
from infinisdk import Q


def test_query_by_parent(infinibox, volume):
    snapshot = volume.create_child()

    [s] = infinibox.volumes.find(parent=volume)
    assert s == snapshot

def test_query_by_parent_none(infinibox, volume):
    [v] = infinibox.volumes.find(parent=None)
    assert v == volume

def test_query_by_pool(infinibox, pool, volume):
    assert [volume] == list(infinibox.volumes.find(pool=pool))
    assert [] == list(infinibox.volumes.find(pool=None))

@new_to_version('3.0')
def test_sort_by_multiple_fields(infinibox, pool):
    vol_ab_thin = infinibox.volumes.create(pool=pool, name='ab', provisioning='THIN')
    vol_bb_thin = infinibox.volumes.create(pool=pool, name='bb', provisioning='THIN')
    vol_aa_thick = infinibox.volumes.create(pool=pool, name='aa', provisioning='THICK')
    vol_ba_thick = infinibox.volumes.create(pool=pool, name='ba', provisioning='THICK')
    assert set(infinibox.volumes.get_all()) == set([vol_ab_thin, vol_bb_thin, vol_aa_thick, vol_ba_thick])

    get_sorted_volumes = lambda *sort_args: list(infinibox.volumes.get_all().sort(*sort_args))
    assert get_sorted_volumes(Q.name, Q.provtype) == [vol_aa_thick, vol_ab_thin, vol_ba_thick, vol_bb_thin]
    assert get_sorted_volumes(Q.provtype, Q.name) == [vol_ab_thin, vol_bb_thin, vol_aa_thick, vol_ba_thick]
    assert get_sorted_volumes(-Q.provtype, Q.name) == [vol_aa_thick, vol_ba_thick, vol_ab_thin, vol_bb_thin]
    assert get_sorted_volumes(-Q.provtype, -Q.name) == [vol_ba_thick, vol_aa_thick, vol_bb_thin, vol_ab_thin]
