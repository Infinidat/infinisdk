from api_object_schema import ObjectAPIBinding
from sentinels import NOTHING
from munch import Munch
from .api.special_values import SpecialValue, RawValue
from .translators_and_types import address_type_factory, host_port_from_api

# pylint: disable=abstract-method

class InfiniSDKBinding(ObjectAPIBinding):

    def get_api_value_from_value(self, system, objtype, obj, value):
        if isinstance(value, SpecialValue):
            if isinstance(value, RawValue):
                return value.generate()
            return value
        return super(InfiniSDKBinding, self).get_api_value_from_value(system, objtype, obj, value)


class InfiniSDKBindingWithSpecialFlags(InfiniSDKBinding):

    def __init__(self, special_flags):
        self._special_flags = special_flags
        super(InfiniSDKBindingWithSpecialFlags, self).__init__()

    def get_api_value_from_value(self, system, objtype, obj, value):
        if value in self._special_flags:
            return value
        return super(InfiniSDKBindingWithSpecialFlags, self).get_api_value_from_value(system, objtype, obj, value)

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        if api_value in self._special_flags:
            return api_value
        return super(InfiniSDKBindingWithSpecialFlags, self).get_value_from_api_value(system, objtype, obj, api_value)

class ReplicaEntityBinding(InfiniSDKBinding):
    def __init__(self, value_for_none=0):
        super(ReplicaEntityBinding, self).__init__()
        self._value_for_none = value_for_none

    def _get_collection(self, obj, system):
        if obj.get_entity_type() == 'FILESYSTEM':
            return system.filesystems
        elif obj.get_entity_type() == 'VOLUME':
            return system.volumes
        else:
            return system.cons_groups

    def get_api_value_from_value(self, system, objtype, obj, value):
        if value is None:
            return self._value_for_none
        if isinstance(value, SpecialValue):
            if isinstance(value, RawValue):
                return value.generate()
            return value
        return value.id

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        if api_value == self._value_for_none or api_value is None:
            return None
        return self._get_collection(obj, system).get_by_id_lazy(api_value)


class RelatedObjectBinding(InfiniSDKBinding):

    def __init__(self, collection_name=None, value_for_none=0):
        super(RelatedObjectBinding, self).__init__()
        self._collection_name = collection_name
        self._value_for_none = value_for_none

    def set_field(self, field):
        super(RelatedObjectBinding, self).set_field(field)
        if not self._collection_name:
            self._collection_name = "{}s".format(field.name)

    def get_api_value_from_value(self, system, objtype, obj, value):
        if value is None:
            return self._value_for_none
        if isinstance(value, SpecialValue):
            if isinstance(value, RawValue):
                return value.generate()
            return value
        return value.id

    def get_api_value_from_object(self, system, objtype, obj):
        if obj is None:
            return self._value_for_none
        return obj.id

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        if api_value == self._value_for_none or api_value is None:
            return None
        return getattr(system, self._collection_name).get_by_id_lazy(api_value)

class RelatedObjectNamedBinding(RelatedObjectBinding):

    def get_api_value_from_value(self, system, objtype, obj, value):
        if isinstance(value, (str, bytes)):
            value = system.objects[self._collection_name].get(name=value)
        return super(RelatedObjectNamedBinding, self).get_api_value_from_value(system, objtype, obj, value)

class ListOfRelatedObjectIDsBinding(RelatedObjectBinding):
    """
    Binding for translating list objects info (dictionaries) to list of objects
    API value = [1, 2]
    InfiniSDK will return:
    value = [<object id=1>, <object id=2>]
    """
    def get_api_value_from_value(self, system, objtype, obj, value):
        if isinstance(value, SpecialValue):
            if isinstance(value, RawValue):
                return value.generate()
            return value
        return [single_value.id for single_value in value]

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        obj_getter = getattr(system, self._collection_name).get_by_id_lazy
        return [obj_getter(obj_id) for obj_id in api_value]


class RelatedComponentBinding(InfiniSDKBinding):

    def __init__(self, collection_name=None, api_index_name=None, value_for_none=NOTHING):
        super(RelatedComponentBinding, self).__init__()
        self._collection_name = collection_name
        self._api_index_name = api_index_name
        self._value_for_none = value_for_none

    def set_field(self, field):
        super(RelatedComponentBinding, self).set_field(field)
        if not self._collection_name:
            self._collection_name = "{}s".format(field.name)
        if not self._api_index_name:
            self._api_index_name = 'index'

    def get_api_value_from_value(self, system, objtype, obj, value):
        if value is None:
            return self._value_for_none
        return value.get_field(self._api_index_name)

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        if api_value == self._value_for_none or api_value is None:
            return None
        kwargs = {self._api_index_name: api_value}
        return system.components[self._collection_name].get(**kwargs)


class ListOfRelatedObjectBinding(InfiniSDKBinding):
    """
    Binding for translating list objects info (dictionaries) to list of objects
    API value = [{'id': 1, k: v, ...}, {'id': 2, k: v, ...}]
    InfiniSDK will return:
    value = [<object id=1>, <object id=2>]
    """
    def __init__(self, collection_name=None):
        super(ListOfRelatedObjectBinding, self).__init__()
        self._collection_name = collection_name

    def set_field(self, field):
        super(ListOfRelatedObjectBinding, self).set_field(field)
        if not self._collection_name:
            self._collection_name = field.name

    def get_api_value_from_value(self, system, objtype, obj, value):
        raise NotImplementedError("This is a read-only binding")

    def _get_collection(self, system):
        return getattr(system, self._collection_name)

    def _get_related_obj(self, system, related_obj_info, obj):  # pylint: disable=unused-argument
        return self._get_collection(system).object_type.construct(system, related_obj_info)

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        return [self._get_related_obj(system, related_obj_info, obj)
                for related_obj_info in api_value]


class ListOfRelatedComponentBinding(ListOfRelatedObjectBinding):
    """
    Binding for translating list components info (dictionaries) to list of objects
    API value = [{'index': 1, k: v, ...}, {'index': 2, k: v, ...}]
    InfiniSDK will return:
    value = [<component index=1>, <component index=2>]
    """

    def _get_collection(self, system):
        return getattr(system.components, self._collection_name)

    def _get_related_obj(self, system, related_obj_info, obj):
        return self._get_collection(system).object_type.construct(system, related_obj_info, obj.id)


class PassthroughBinding(InfiniSDKBinding):

    def get_api_value_from_value(self, system, objtype, obj, value):
        if isinstance(value, RawValue):
            return value.generate()
        return value

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        return api_value


class ListToDictBinding(InfiniSDKBinding):
    """
    Binding for simple api quirks, where api expects the following:
    [ { "name" : value1 }, { "name" : value2 } ]
    InfiniSDK will use a simple list of strings:
    [ value1, value2 ]
    """
    def __init__(self, key):
        super(ListToDictBinding, self).__init__()
        self.key = key

    def get_value_from_api_value(self, system, objtype, obj, api_value):
        return [d[self.key] for d in api_value]

    def get_api_value_from_value(self, system, objtype, obj, value):
        if isinstance(value, SpecialValue):
            if isinstance(value, RawValue):
                return value.generate()
            return value
        return [{self.key:val} for val in value]


class InitiatorAddressBinding(InfiniSDKBinding):
    def get_value_from_api_object(self, system, objtype, obj, api_obj): # pylint: disable=unused-argument, no-self-use
        return host_port_from_api(api_obj)


class InitiatorTargetsBinding(InfiniSDKBinding):
    def get_value_from_api_object(self, system, objtype, obj, api_obj): # pylint: disable=unused-argument
        initiator_type = api_obj.get('type') or obj.get_type(from_cache=True)
        target_type = address_type_factory(initiator_type)
        result = []
        for target_info in api_obj[self._field.api_name]:
            target = Munch()
            if system.compat.has_iscsi():
                target_address = target_info.pop('address')
                target.node = system.components.nodes.get(index=target_info.pop('node_id'))
                target.update(target_info)
            else:
                target_address = target_info
            target.address = target_type(target_address)
            result.append(target)
        return result
