def test_get_assigned_entities(infinibox, volume, volume_qos_policy):
    volume_qos_policy.assign_entity(volume)
    assert volume_qos_policy.get_assigned_entities().to_list() == [volume]
    assert infinibox.qos_policies.get_assigned_entities().to_list() == [volume]
