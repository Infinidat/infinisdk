from ..conftest import relevant_from_version


@relevant_from_version('2.2')
def test_initiators_sanity(infinibox):
    assert isinstance(infinibox.initiators.to_list(), list)
