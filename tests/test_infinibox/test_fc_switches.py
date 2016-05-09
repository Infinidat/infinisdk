from ..conftest import new_to_version


@new_to_version('3.0')
def test_fc_swithches_query(infinibox):
    fc_switch = infinibox.fc_switches.choose()
    assert fc_switch.get_vendor() == 'Cisco'
