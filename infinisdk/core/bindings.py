from api_object_schema import ObjectAPIBinding

from .api.special_values import SpecialValue,RawValue


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

    def get_value_from_api_value(self, system, objtype, obj, value):
        if value in self._special_flags:
            return value
        return super(InfiniSDKBindingWithSpecialFlags, self).get_value_from_api_value(system, objtype, obj, value)


class RelatedObjectBinding(InfiniSDKBinding):

    def __init__(self, collection_name=None, value_for_none=0):
        super(RelatedObjectBinding, self).__init__()
        self._collection_name = collection_name
        self._value_for_none = value_for_none

    def set_field(self, field):
        super(RelatedObjectBinding, self).set_field(field)
        if not self._collection_name:
            self._collection_name = "{0}s".format(field.name)

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

    def get_value_from_api_value(self, system, objtype, obj, value):
        if value == self._value_for_none or value is None:
            return None
        return getattr(system, self._collection_name).get_by_id_lazy(value)


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

    def get_value_from_api_value(self, system, objtype, obj, value):
        obj_getter = getattr(system, self._collection_name).get_by_id_lazy
        return [obj_getter(obj_id) for obj_id in value]


class RelatedComponentBinding(InfiniSDKBinding):

    def __init__(self, collection_name=None, api_index_name=None):
        super(RelatedComponentBinding, self).__init__()
        self._collection_name = collection_name
        self._api_index_name = api_index_name

    def set_field(self, field):
        super(RelatedComponentBinding, self).set_field(field)
        if not self._collection_name:
            self._collection_name = "{0}s".format(field.name)
        if not self._api_index_name:
            self._api_index_name = 'index'

    def get_api_value_from_value(self, system, objtype, obj, value):
        return value.get_field(self._api_index_name)

    def get_value_from_api_value(self, system, objtype, obj, value):
        kwargs = {self._api_index_name: value}
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

    def _get_related_obj(self, system, related_obj_info, obj):
        return self._get_collection(system).object_type.construct(system, related_obj_info)

    def get_value_from_api_value(self, system, objtype, obj, value):
        return [self._get_related_obj(system, related_obj_info, obj)
                for related_obj_info in value]


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

    def get_value_from_api_value(self, system, objtype, obj, value):
        return value


class ListToDictBinding(InfiniSDKBinding):
    """
    Binding for simple api quircks, where api expects the following:
    [ { "name" : value1 }, { "name" : value2 } ]
    InfiniSDK will use a simple list of strings:
    [ value1, value2 ]
    """
    def __init__(self, key):
        super(ListToDictBinding, self).__init__()
        self.key = key

    def get_value_from_api_value(self, system, objtype, obj, value):
        return [d[self.key] for d in value]

    def get_api_value_from_value(self, system, objtype, obj, value):
        if isinstance(value, SpecialValue):
            if isinstance(value, RawValue):
                return value.generate()
            return value
        return [{self.key:val} for val in value]
