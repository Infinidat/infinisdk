import pytest
import re
from infinisdk.core.api.special_values import OMIT, RawValue
from infinisdk.core.bindings import RelatedObjectBinding, PassthroughBinding, ListToDictBinding, RelatedSubObjectBinding
from infinisdk.core.exceptions import InfiniSDKRuntimeException
from infinisdk.core.utils.resolvers import schedules_resolver


@pytest.mark.parametrize("special_value", [OMIT, RawValue('some_string')])
@pytest.mark.parametrize("binding", [RelatedObjectBinding(), PassthroughBinding(), ListToDictBinding('key')])
def test_omit(binding, special_value):
    #infinibox.volumes.create(pool=OMIT)
    api_value = binding.get_api_value_from_value(system=None, objtype=None, obj=None, value=special_value)
    if isinstance(special_value, RawValue):
        assert api_value is not special_value
    else:
        assert api_value is special_value


@pytest.mark.parametrize("special_value", [1, "1"])
@pytest.mark.parametrize("binding", [RelatedObjectBinding(), PassthroughBinding(), ListToDictBinding('key')])
def test_raw_value(binding, special_value):
    api_value = binding.get_api_value_from_value(system=None, objtype=None, obj=None, value=RawValue(special_value))
    assert not isinstance(api_value, RawValue)


def test_related_subobject_binding_wrong_specification():
    with pytest.raises(AssertionError, match=re.escape("Subobjects need to be specified as 'parents/childs'")):
        RelatedSubObjectBinding("parent-child").get_value_from_api_value(system=None, objtype=None, obj=None, api_value=23)


def test_related_subobject_binding_too_nested():
    with pytest.raises(AssertionError, match=re.escape("Illegal name, child/grandchild")):
        RelatedSubObjectBinding("parent/child/grandchild").get_value_from_api_value(system=None, objtype=None, obj=None, api_value=23)


def test_related_subobject_binding_no_collection(infinibox):
    with pytest.raises(InfiniSDKRuntimeException, match=re.escape("No such collection (parents)")):
        RelatedSubObjectBinding("parents/child").get_value_from_api_value(system=infinibox, objtype=None, obj=None, api_value=23)


def test_related_subobject_binding(infinibox, volume_snapshot_and_schedule):
    expected_obj = volume_snapshot_and_schedule[1]
    assert RelatedSubObjectBinding("snapshot_policies/schedules").get_value_from_api_value(system=infinibox, objtype=None, obj=volume_snapshot_and_schedule[0], api_value=expected_obj.get_id()) == expected_obj


def test_related_subobject_binding_resolver(infinibox, volume_from_cg_snapshot_and_schedule):
    snapshot_volume = volume_from_cg_snapshot_and_schedule[0]
    expected_obj = volume_from_cg_snapshot_and_schedule[1]
    assert RelatedSubObjectBinding("snapshot_policies/schedules", child_collection_resolver=schedules_resolver).get_value_from_api_value(system=infinibox, objtype=None, obj=snapshot_volume, api_value=expected_obj.get_id()) == expected_obj
    assert snapshot_volume.get_created_by_schedule() == expected_obj 
    assert snapshot_volume.get_created_by_schedule_name() == expected_obj.get_name()
