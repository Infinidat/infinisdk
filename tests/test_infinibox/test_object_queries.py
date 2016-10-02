from infinisdk import Q


def test_query_with_q(infinibox, volume):
    [v] = infinibox.volumes.find(Q.size >= volume.get_size())
    assert v == volume


def test_query_to_list(type_binder):
    objs = type_binder.find().to_list()
    assert isinstance(objs, list)
    assert objs == list(type_binder)


def test_type_binder_to_list(type_binder):
    objs = type_binder.to_list()
    assert isinstance(objs, list)
    assert objs == list(type_binder)


def test_query_count(type_binder):
    assert type_binder.count() == type_binder.find().count()


def test_null_checking_with_equality(infinibox):
    query = infinibox.volumes.find(Q.cons_group == None)  # pylint: disable=singleton-comparison
    assert str(query).endswith('cg_id=eq%3Anull')

def test_query_with_iterables(infinibox, volume):
    for iterable in [[volume.get_id()],
                     {volume.get_id():volume}.keys(),
                     set([volume.get_id()])]:
        query = infinibox.volumes.find(Q.id.in_(iterable))
        assert str(query).endswith('id=in%3A%28{}%29'.format(volume.get_id()))
