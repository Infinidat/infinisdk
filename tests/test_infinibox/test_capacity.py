from infinibox_sysdefs import latest as defs
from capacity import Capacity
from ..conftest import versioning_requiremnts


def test_physical_capacity(infinibox):
    assert isinstance(infinibox.capacities.get_free_physical_capacity(), Capacity)
    assert isinstance(infinibox.capacities.get_total_physical_capacity(), Capacity)
    pool_reserve = defs.internal.default_pool_reserved_capacity.roundup(
        defs.internal.num_vus * defs.internal.section_size)
    assert infinibox.capacities.get_free_physical_capacity() + pool_reserve == \
        infinibox.capacities.get_total_physical_capacity()


def test_virtual_capacity(infinibox):
    assert isinstance(infinibox.capacities.get_free_virtual_capacity(), Capacity)
    assert isinstance(infinibox.capacities.get_total_virtual_capacity(), Capacity)
    assert infinibox.capacities.get_free_virtual_capacity() == infinibox.capacities.get_total_virtual_capacity()


@versioning_requiremnts(relevant_from='3.0')
def test_get_fields(infinibox):
    capacity_fields = ['total_physical_capacity', 'free_physical_space', 'total_virtual_capacity', 'free_virtual_space', 'total_spare_bytes', 'used_spare_bytes', 'used_dynamic_spare_bytes', 'total_allocated_physical_space']
    int_fields = ["total_spare_partitions", "used_spare_partitions", "used_dynamic_spare_partitions", "dynamic_spare_drive_cost"]
    res_capacities = infinibox.capacities.get_fields(capacity_fields)
    res_ints = infinibox.capacities.get_fields(int_fields)
    assert len(res_capacities) == 8
    assert len(res_ints) == 4
    assert all([k in capacity_fields for k in res_capacities.keys()]) and all([k in int_fields for k in res_ints.keys()])
    assert all([isinstance(v, Capacity) for v in res_capacities.values()])
    assert all([isinstance(v, int) for v in res_ints.values()])
