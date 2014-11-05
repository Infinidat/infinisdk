import pytest
from infinisdk.core.api.special_values import OMIT, RawValue
from infinisdk.core.bindings import RelatedObjectBinding, PassthroughBinding, ListToDictBinding

@pytest.mark.parametrize("special_value", [OMIT, RawValue('some_string')])
@pytest.mark.parametrize("binding", [RelatedObjectBinding(), PassthroughBinding(), ListToDictBinding('key')])
def test_omit(binding, special_value):
    #infinibox.volumes.create(pool=OMIT)
    api_value = binding.get_api_value_from_value(system=None, objtype=None, obj=None, value=special_value)
    assert api_value is special_value


@pytest.mark.parametrize("special_value", [1, "1"])
@pytest.mark.parametrize("binding", [RelatedObjectBinding(), PassthroughBinding(), ListToDictBinding('key')])
def test_raw_value(binding, special_value):
    api_value = binding.get_api_value_from_value(system=None, objtype=None, obj=None, value=RawValue(special_value))
    assert isinstance(api_value, RawValue)
