import pytest
from capacity import Capacity, TB
import flux

from infinisdk.core.exceptions import APICommandFailed
from infinisdk.infinibox.volume import Volume
from infinisdk.infinibox.pool import Pool
from infinisdk.infinibox.scsi_serial import SCSISerial

from ..conftest import create_volume, add_internal_volumes_to_system, create_internal_volumes


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
    child = volume.create_snapshot()
    assert child.get_parent() == volume
    assert volume.has_children()

    assert not hasattr(volume, 'is_has_children')


def test_write_protection(volume):
    assert not volume.is_write_protected()
    volume.enable_write_protection()
    assert volume.is_write_protected()


def test_unmap_volume_which_mapped_to_multiple_hosts(infinibox, volume):
    assert not volume.is_mapped()
    host_count = 3
    for _ in range(host_count):
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

def test_create_volume_with_pool_name(infinibox, pool):
    volume = create_volume(infinibox, pool=pool.get_name())
    assert volume.get_pool() == pool


def test_promote_snapshot(volume, pool):
    # the volume fixture got the pool id of the pool fixture
    volume_snapshot = volume.create_snapshot()
    promoted_volume_snapshot = volume_snapshot.promote_snapshot()

    assert promoted_volume_snapshot == volume_snapshot
    assert promoted_volume_snapshot.get_type() == "MASTER"
    assert promoted_volume_snapshot.get_pool() == pool


@add_internal_volumes_to_system(number_of_internal_volumes_type_master=1, number_of_internal_volumes_type_snapshot=1)
def test_get_all_internals_dont_filter_by_type(infinibox):
    all_internal_volumes = infinibox.volumes.get_all_internals()
    assert len(all_internal_volumes) == 2


@add_internal_volumes_to_system(number_of_internal_volumes_type_master=1, number_of_internal_volumes_type_snapshot=2)
def test_get_all_internals_filter_by_type(infinibox):
    master_internal_volumes = infinibox.volumes.get_all_internals(internal_type="master")
    snapshot_internal_volumes = infinibox.volumes.get_all_internals(internal_type="snapshot")

    assert len(master_internal_volumes) == 1
    assert len(snapshot_internal_volumes) == 2
    

def test_get_all_internals(infinibox, volume):
    create_internal_volumes(
        infinibox=infinibox, 
        volume=volume, 
        internal_volume_type='snapshot',
        number_of_snapshots=2
    )
    
    internal_volumes = volume.get_all_internals()
    assert len(internal_volumes) == 2


@add_internal_volumes_to_system(number_of_internal_volumes_type_snapshot=20)
def test_get_all_internals_api_pages(infinibox):
    all_internal_volumes_page_1 = infinibox.volumes.get_all_internals(page_size=10, page=1)
    all_internal_volumes_page_2 = infinibox.volumes.get_all_internals(page_size=10, page=2)

    assert len(all_internal_volumes_page_1) == 10
    assert len(all_internal_volumes_page_2) == 10
    assert all_internal_volumes_page_1 != all_internal_volumes_page_2

def test_bulk_update_ssa_express_enabled(infinibox, create_many_volumes):
    volumes = create_many_volumes(10)
    assert len(infinibox.get_ssa_express_active_datasets()) == 0
    infinibox.volumes.bulk_update(entities=volumes, ssa_express_enabled=True)
    flux.current_timeline.sleep(100)
    assert len(infinibox.get_ssa_express_active_datasets()) == 10

def test_create_volume_snapshot_with_remote_snapshot_retention_and_remote_snapshot_retention_lock(replica):    
    volume_snapshot = replica.get_local_entity().create_snapshot(remote_snapshot_retention=86400, remote_snapshot_retention_lock=86400)
    
    volume_snapshot_remote_snapshot_retention = volume_snapshot.get_remote_snapshot_retention()
    assert volume_snapshot_remote_snapshot_retention == 86400
    
    volume_snapshot_remote_snapshot_retention_lock = volume_snapshot.get_remote_snapshot_retention_lock()
    assert volume_snapshot_remote_snapshot_retention_lock == 86400
