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
