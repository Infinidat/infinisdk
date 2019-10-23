
def test_get_name(cluster):
    assert cluster.get_name().startswith('cluster_')


def test_update_name(cluster):
    curr_name = cluster.get_name()
    new_name = 'other_cluster_name'
    cluster.update_name(new_name)

    assert curr_name != new_name
    assert cluster.get_name() == new_name


def test_creation(infinibox, cluster):
    kwargs = {'name': 'some_cluster_name'}
    cluster = infinibox.host_clusters.create(**kwargs)

    for k, v in kwargs.items():
        assert cluster._cache[k] == v  # pylint: disable=protected-access
    assert cluster.get_hosts() == []

    cluster.delete()
    assert not cluster.is_in_system()


def test_hosts_operations(infinibox, cluster, request):
    assert cluster.get_hosts() == []
    host = infinibox.hosts.create()
    request.addfinalizer(host.delete)

    cluster.add_host(host)
    hosts = cluster.get_hosts()
    assert len(hosts) == 1
    assert hosts[0] == host

    cluster.remove_host(host)
    hosts = cluster.get_hosts()
    assert len(hosts) == 0
