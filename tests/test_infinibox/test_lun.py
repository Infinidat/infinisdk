import pytest


def test_no_luns_mapped(infinibox, host, cluster):
    luns = host.get_luns()
    assert len(luns) == 0

    pool = infinibox.pools.create()
    vol = infinibox.volumes.create(pool=pool)
    assert (not host.is_volume_mapped(vol))

def test_map_volume_to_cluster(infinibox, host, cluster, volume):
    assert (not volume.is_mapped())

    cluster.map_volume(volume)
    assert volume.is_mapped()

    luns = cluster.get_luns()
    assert len(luns) == 1
    assert cluster.is_volume_mapped(volume)

    lu = list(luns)[0]
    assert lu.get_volume() == volume
    volume_lun = volume.get_lun()
    assert lu == volume_lun
    assert lu == luns[int(volume_lun)]
    assert lu.get_host() is None
    assert lu.get_cluster() == cluster

    lu.unmap()
    assert len(cluster.get_luns()) == 0
    assert (not volume.is_mapped())

def test_map_volume_to_host(infinibox, host, cluster, volume):
    assert (not volume.is_mapped())

    host.map_volume(volume, 2)
    assert volume.is_mapped()

    luns = host.get_luns()
    assert len(luns) == 1

    lu = list(luns)[0]
    assert lu.get_lun() == int(lu)
    volume_lun = volume.get_lun()
    assert lu.get_volume() == volume
    assert lu == luns[int(volume_lun)]
    assert lu == volume.get_lun()
    assert lu.get_cluster() is None
    assert lu.get_host() == host

    lu.unmap()
    assert len(host.get_luns()) == 0
    assert (not volume.is_mapped())

def test_multiple_luns_mapping_objects(infinibox, host, cluster, volume1, volume2):
    host.map_volume(volume1)

    cluster.map_volume(volume2)

    host_lus = host.get_luns()
    cluster_lus = cluster.get_luns()

    assert len(host_lus) == 1
    assert len(cluster_lus) == 1

    host_lu = list(host_lus)[0]
    assert list(host_lus[volume1])[0] == host_lu

    cluster_lu = list(cluster_lus)[0]
    assert list(cluster_lus[volume2])[0] == cluster_lu

    with pytest.raises(KeyError):
        cluster_lus[volume1]

    assert cluster_lus.get(host_lu.get_lun(), None) == None
    assert host_lus.get(host_lu.get_lun(), None) == host_lu

    assert (not cluster_lu in host_lus)

    assert host_lu != cluster_lu

    host_lu.delete()
    cluster_lu.delete()
