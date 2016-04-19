
def test_fc_swithches_query(infinibox):
    fc_switch = infinibox.fc_switches.choose()
    assert fc_switch.get_vendor() == 'Cisco'
