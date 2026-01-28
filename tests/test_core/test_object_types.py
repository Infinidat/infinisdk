def test_system_types(infinibox):
    assert infinibox.types.volume is infinibox.types.Volume
    assert infinibox.types.volume is infinibox.volumes.object_type
