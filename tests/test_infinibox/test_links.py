from ..conftest import relevant_from_version


@relevant_from_version('2.0')
def test_link_creation(link):  # pylint: disable=unused-argument
    pass


@relevant_from_version('2.0')
def test_link_get_fields(link):
    link.get_fields()


@relevant_from_version('2.0')
def test_link_state(link):
    assert link.get_link_state()


@relevant_from_version('2.0')
def test_link_remote_system_name(link, secondary_infinibox):
    assert link.get_remote_system_name() == secondary_infinibox.get_name()


@relevant_from_version('2.0')
def test_link_remote_system_serial_number(link, secondary_infinibox):
    assert link.get_remote_system_serial_number() == secondary_infinibox.get_serial()


@relevant_from_version('2.0')
def test_link_get_remote_link_id(infinibox, secondary_infinibox, link):  # pylint: disable=unused-argument
    remote_link_id = link.get_remote_link_id()
    remote_link = secondary_infinibox.links.get_by_id_lazy(remote_link_id)
    assert remote_link.is_in_system()
