from capacity import Capacity
from infinisdk.infinibox.volume import Volume
from infinisdk.infinibox.pool import Pool
from infinisdk.infinibox.scsi_serial import SCSISerial


def test_unmapping(infinibox, mapped_volume):
    assert mapped_volume.get_logical_units()
    mapped_volume.unmap()
    assert not mapped_volume.get_logical_units()

def test_write_protection(volume):
    assert not volume.get_write_protected()
    volume.update_write_protected(True)
    assert volume.get_write_protected()


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


def test_move_volume(infinibox, volume):
    # TODO: support with_capacity parameter (TESTINF-3058)
    with_capacity = False
    oldpool = volume.get_pool()
    old_virt_capacity = oldpool.get_virtual_capacity()
    newpool = infinibox.pools.create()
    new_virt_capacity = newpool.get_virtual_capacity()
    assert newpool != oldpool
    volume.move_pool(newpool, with_capacity=with_capacity)
    assert volume.get_pool() == newpool
    assert volume not in oldpool.get_volumes()
    assert volume in newpool.get_volumes()
    vol_size = volume.get_size()
    if with_capacity:
        assert oldpool.get_virtual_capacity() == old_virt_capacity - vol_size
        assert newpool.get_virtual_capacity() == new_virt_capacity + vol_size
    else:
        assert oldpool.get_virtual_capacity() == old_virt_capacity
        assert newpool.get_virtual_capacity() == new_virt_capacity
