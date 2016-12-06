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
    fileds = ['total_virtual_capacity', 'total_physical_capacity']
    res = infinibox.capacities.get_fields(fileds)
    assert len(res) == 2
    assert all([k in fileds for k in res.keys()])
    assert all([isinstance(v, Capacity) for v in res.values()])
