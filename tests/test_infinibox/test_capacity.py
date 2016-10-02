from infinibox_sysdefs import latest as defs
from capacity import Capacity


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
