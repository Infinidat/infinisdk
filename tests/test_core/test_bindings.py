import pytest
from infinisdk.core.api.special_values import OMIT
from infinisdk.core.bindings import RelatedObjectBinding, PassthroughBinding, ListToDictBinding


@pytest.mark.parametrize("binding", [RelatedObjectBinding(), PassthroughBinding(), ListToDictBinding('key')])
def test_debugging(binding):
    #infinibox.volumes.create(pool=OMIT)
    api_value = binding.get_api_value_from_value(system=None, objtype=None, obj=None, value=OMIT)
    assert api_value is OMIT
