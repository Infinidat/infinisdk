from ..conftest import new_to_version


@new_to_version('2.2')
def test_initiators_sanity(infinibox):
    assert isinstance(infinibox.initiators.to_list(), list)
