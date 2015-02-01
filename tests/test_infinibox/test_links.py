from ..conftest import new_to_version


@new_to_version('2.0')
def test_link_creation(link):
    pass


@new_to_version('2.0')
def test_link_get_fields(link):
    link.get_fields()


@new_to_version('2.0')
def test_link_get_remote_link_id(infinibox, secondary_infinibox, link):
    remote_link_id = link.get_remote_link_id()
    remote_link = secondary_infinibox.links.get_by_id_lazy(remote_link_id)
    assert remote_link.is_in_system()
