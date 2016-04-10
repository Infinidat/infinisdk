import pytest
from ..conftest import new_to_version
from infinisdk._compat import xrange
from capacity import Capacity, TB
from infinisdk.infinibox.volume import Volume
from infinisdk.infinibox.pool import Pool
from infinisdk.infinibox.scsi_serial import SCSISerial


def test_unmapping(infinibox, mapped_volume):
    assert mapped_volume.is_mapped()
    assert mapped_volume.get_logical_units()
    mapped_volume.unmap()
    assert not mapped_volume.is_mapped()
    assert not mapped_volume.get_logical_units()


def test_has_children(infinibox, volume):
    assert not volume.has_children()
    s = volume.create_child()
    assert volume.has_children()

    assert not hasattr(volume, 'is_has_children')


def test_write_protection(volume):
    assert not volume.is_write_protected()
    volume.update_write_protected(True)
    assert volume.is_write_protected()


def test_unmap_volume_which_mapped_to_multiple_hosts(infinibox, volume):
    assert not volume.is_mapped()
    host_count = 3
    for _ in xrange(host_count):
        host = infinibox.hosts.create()
        host.map_volume(volume)
    assert len(volume.get_logical_units()) == host_count
    volume.unmap()
    assert not volume.is_mapped()


def test_serial(infinibox, volume):
    assert isinstance(volume.get_serial(), SCSISerial)


def test_allocated(infinibox, volume):
    assert isinstance(volume.get_allocated(), Capacity)


def test_field_types():
    assert Volume.fields.parent.type.type is Volume
    assert Volume.fields.pool.type.type is Pool


def test_create_many(infinibox, pool):

    name = 'some_name'
    vols = infinibox.volumes.create_many(pool=pool, count=5, name=name)

    assert len(vols) == 5

    for index, vol in enumerate(vols, start=1):
        assert vol.get_name() == '{0}_{1}'.format(name, index)


@pytest.mark.parametrize('with_capacity', [True, False])
def test_move_volume(infinibox, with_capacity):
    if with_capacity and int(infinibox.compat.get_version_major()) < 2:
        pytest.skip('infinisim does not support with_capacity for this version')
    oldpool = infinibox.pools.create(virtual_capacity=10*TB, physical_capacity=10*TB)
    volume = infinibox.volumes.create(pool=oldpool, size=TB)
    old_virt_capacity = oldpool.get_virtual_capacity()
    newpool = infinibox.pools.create(virtual_capacity=10*TB, physical_capacity=10*TB)
    new_virt_capacity = newpool.get_virtual_capacity()
    assert newpool != oldpool
    volume.move_pool(newpool, with_capacity=with_capacity)
    assert volume.get_pool() == newpool
    assert volume not in oldpool.get_volumes()
    assert volume in newpool.get_volumes()
    if with_capacity:
        assert oldpool.get_virtual_capacity(from_cache=False) < old_virt_capacity
        assert newpool.get_virtual_capacity(from_cache=False) > new_virt_capacity
    else:
        assert oldpool.get_virtual_capacity(from_cache=False) == old_virt_capacity
        assert newpool.get_virtual_capacity(from_cache=False) == new_virt_capacity
