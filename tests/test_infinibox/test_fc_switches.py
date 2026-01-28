from ..conftest import relevant_from_version


@relevant_from_version('3.0')
def test_fc_swithches_query(infinibox):
    fc_switch = infinibox.fc_switches.choose()
    assert fc_switch.get_vendor() in ('Cisco', 'Brocade')
