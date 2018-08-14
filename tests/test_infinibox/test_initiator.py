def test_initiators_sanity(infinibox):
    assert isinstance(infinibox.initiators.to_list(), list)
