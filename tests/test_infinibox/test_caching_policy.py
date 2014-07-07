import pytest


@pytest.mark.parametrize('enable_caching', [True, False])
def test_caching(infinibox, pool, volume, infinisim_volume, enable_caching):

    if enable_caching:
        infinibox.enable_caching()
    else:
        infinibox.disable_caching()

    old_size = volume.get_size()
    assert infinisim_volume.get_size() == old_size
    infinisim_volume.set_size(old_size * 2)
    if enable_caching:
        assert volume.get_size() == old_size
    else:
        assert volume.get_size() != old_size


@pytest.fixture
def infinisim_volume(volume, infinibox_simulator):
    [returned] = infinibox_simulator.volumes
    assert returned.id == volume.id
    return returned
