import gc


class MockedSystem(object):
    def __init__(self, name):
        self.get_name = lambda: name


def _assert_expected_systems(infinibox, expected_systems):
    expected_names = set(s.get_name() for s in expected_systems)
    for r_system in infinibox.iter_related_systems():
        name = r_system.get_name()
        assert name in expected_names
        expected_names.remove(name)

    assert not expected_names


def test_multiple_related(infinibox):
    secondary = MockedSystem('secondary-system')
    third = MockedSystem('third-system')
    infinibox.register_related_system(secondary)
    infinibox.register_related_system(third)
    _assert_expected_systems(infinibox, [secondary, third])
    infinibox.unregister_related_system(secondary)
    _assert_expected_systems(infinibox, [third])
    infinibox.unregister_related_system(third)
    _assert_expected_systems(infinibox, [])
    infinibox.unregister_related_system(third)
    _assert_expected_systems(infinibox, [])


def test_garbage_collection(infinibox):
    secondary = MockedSystem('secondary-system')
    third = MockedSystem('third-system')
    infinibox.register_related_system(secondary)
    infinibox.register_related_system(third)
    _assert_expected_systems(infinibox, [secondary, third])

    del secondary
    assert gc.collect() > 0

    assert len(infinibox._related_systems) == 2
    _assert_expected_systems(infinibox, [third])
    assert len(infinibox._related_systems) == 1
