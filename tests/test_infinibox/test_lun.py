import pytest
from infinisdk.core.exceptions import CacheMiss


def test_unmap_clustered_lun(host, cluster, volume):
    cluster.add_host(host)
    vol_lu = cluster.map_volume(volume)

    logical_units = volume.get_logical_units()
    assert len(logical_units) == 2
    assert set(lu.get_lun() for lu in logical_units) == set([vol_lu.lun])

    vol_lu.unmap()
    assert not volume.get_logical_units()

def test_unmap_cluster_with_two_hosts(infinibox, cluster, volume):
    for _ in range(2):
        host = infinibox.hosts.create()
        cluster.add_host(host)
    cluster.map_volume(volume)
    volume.get_lun(cluster)
    assert volume.is_mapped()
    cluster.unmap_volume(volume=volume)
    assert not volume.is_mapped()


def test_unmap_lun_twice(logical_unit):
    logical_unit.unmap()
    logical_unit.unmap()

def test_system_luns(infinibox, host, volume):
    lu = host.map_volume(volume)

    assert list(infinibox.luns) == [lu]

    lu.delete()

def test_system_luns_with_cluster(infinibox, host, cluster, volume):
    lu = cluster.map_volume(volume)

    cluster.add_host(host)

    assert list(infinibox.luns) == [lu]

    lu.delete()

def test_no_luns_mapped(infinibox, host):
    luns = host.get_luns()
    assert len(luns) == 0

    pool = infinibox.pools.create()
    vol = infinibox.volumes.create(pool=pool)
    assert (not host.is_volume_mapped(vol))

def test_mapping_object(mapping_object, volume):
    lu = mapping_object.map_volume(volume)
    assert volume.get_lun(mapping_object) == lu
    assert lu.mapping_object == lu.get_mapping_object() == mapping_object
    lu.unmap()

def test_map_volume_to_cluster(cluster, volume):
    assert (not volume.is_mapped())

    cluster.map_volume(volume)
    volume.invalidate_cache()
    assert volume.is_mapped()

    luns = cluster.get_luns()
    assert len(luns) == 1
    assert cluster.is_volume_mapped(volume)

    lu = list(luns)[0]
    assert lu.get_volume() == volume
    volume_lus = volume.get_logical_units()
    assert len(volume_lus) == 1
    volume_lu = next(iter(volume_lus))
    assert lu == volume_lu
    assert lu == luns[int(volume_lu)]
    assert lu.get_host() is None
    assert lu.get_cluster() == cluster

    lu.unmap()
    cluster.invalidate_cache()
    volume.invalidate_cache()
    assert len(cluster.get_luns()) == 0
    assert (not volume.is_mapped())


def test_lun_is_clustered(host, cluster, volume):
    lu = host.map_volume(volume)
    assert not lu.is_clustered()

    lu.unmap()

    lu = cluster.map_volume(volume)
    assert lu.is_clustered()

    cluster.add_host(host)

    [lu] = host.get_luns()
    assert lu.is_clustered()

    lu.unmap()


def test_map_volume_to_host(host, volume):
    assert (not volume.is_mapped())

    host.map_volume(volume, 2)
    volume.invalidate_cache()
    assert volume.is_mapped()

    luns = host.get_luns()
    assert len(luns) == 1

    lu = list(luns)[0]
    assert lu.get_lun() == int(lu)
    volume_lus = volume.get_logical_units()
    assert len(volume_lus) == 1
    volume_lu = next(iter(volume_lus))
    assert lu == volume_lu

    assert lu.get_volume() == volume
    assert lu == luns[int(volume_lu)]
    assert lu == volume.get_lun(host)
    assert lu.get_cluster() is None
    assert lu.get_host() == host

    lu.unmap()
    host.invalidate_cache()
    volume.invalidate_cache()
    assert len(host.get_luns()) == 0
    assert (not volume.is_mapped())


def test_multiple_luns_mapping_objects(host, cluster, volume1, volume2):
    host.map_volume(volume1)

    cluster.map_volume(volume2)

    host_lus = host.get_luns()
    cluster_lus = cluster.get_luns()

    assert len(host_lus) == 1
    assert len(cluster_lus) == 1

    host_lu = list(host_lus)[0]
    assert host_lus[volume1] == host_lu

    cluster_lu = list(cluster_lus)[0]
    assert cluster_lus[volume2] == cluster_lu

    with pytest.raises(KeyError):
        cluster_lus[volume1]  # pylint: disable=pointless-statement

    assert cluster_lus.get(host_lu.get_lun(), None) is None
    assert host_lus.get(host_lu.get_lun(), None) == host_lu

    assert (not cluster_lu in host_lus)

    assert host_lu != cluster_lu

    host_lu.delete()
    cluster_lu.delete()

def test_get_specific_lun(infinibox, mapping_object, volume1, volume2):
    lu_from_post = mapping_object.map_volume(volume1)
    with pytest.raises(CacheMiss):
        lu_from_getter = mapping_object.get_lun(int(lu_from_post), fetch_if_not_cached=False)
    lu_from_getter = mapping_object.get_lun(int(lu_from_post), fetch_if_not_cached=True)
    assert lu_from_post == lu_from_getter
    assert mapping_object._cache.get('luns') is None  # pylint: disable=protected-access
    mapping_object.get_luns()
    assert len(mapping_object._cache.get('luns')) == 1  # pylint: disable=protected-access

    infinibox.enable_caching()
    mapping_object.map_volume(volume2)


@pytest.fixture
def logical_unit(volume, mapping_object):
    mapping_object.map_volume(volume)
    [returned] = volume.get_logical_units()
    return returned
