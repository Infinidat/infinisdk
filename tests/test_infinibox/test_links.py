from ..conftest import new_to_version


@new_to_version('2.0')
def test_link_creation(link):
    pass


@new_to_version('2.0')
def test_link_get_fields(link):
    link.get_fields()


@new_to_version('2.0')
def test_link_state(link):
    assert link.get_link_state()


@new_to_version('2.0')
def test_link_remote_system_name(link, secondary_infinibox):
    assert link.get_remote_system_name() == secondary_infinibox.get_name()


@new_to_version('2.0')
def test_link_remote_system_serial(link, secondary_infinibox):
    assert link.get_remote_system_serial() == secondary_infinibox.get_serial()


@new_to_version('2.0')
def test_link_get_remote_link_id(infinibox, secondary_infinibox, link):
    remote_link_id = link.get_remote_link_id()
    remote_link = secondary_infinibox.links.get_by_id_lazy(remote_link_id)
    assert remote_link.is_in_system()
