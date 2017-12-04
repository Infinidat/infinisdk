import pytest
from infinisdk._compat import xrange  # pylint: disable=redefined-builtin
from capacity import Capacity, TB

from infinisdk.core.exceptions import APICommandFailed
from infinisdk.infinibox.volume import Volume
from infinisdk.infinibox.pool import Pool
from infinisdk.infinibox.scsi_serial import SCSISerial


def test_is_in_cons_group(volume, cg):
    assert not volume.is_in_cons_group()
    cg.add_member(volume)
    assert volume.is_in_cons_group()

def test_unmapping(mapped_volume):
    assert mapped_volume.is_mapped()
    assert mapped_volume.get_logical_units()
    mapped_volume.unmap()
    assert not mapped_volume.is_mapped()
    assert not mapped_volume.get_logical_units()


def test_has_children(volume):
    assert not volume.has_children()
    child = volume.create_child()
    assert child.get_parent() == volume
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


def test_serial(volume):
    assert isinstance(volume.get_serial(), SCSISerial)


def test_allocated(volume):
    assert isinstance(volume.get_allocated(), Capacity)


def test_field_types():
    # pylint: disable=no-member
    assert Volume.fields.parent.type.type is Volume
    assert Volume.fields.pool.type.type is Pool


def test_is_supported(infinibox):
    # Testing Volume.is_supported because this binder exist on all infinibox versions
    assert Volume.is_supported(infinibox)
    assert infinibox.volumes.is_supported()


def test_delete_delted_object(volume):
    # Testing Volume.is_supported because this binder exist on all infinibox versions
    volume.delete()
    assert not volume.is_in_system()
    with pytest.raises(APICommandFailed):
        volume.delete()
    volume.safe_delete()



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
