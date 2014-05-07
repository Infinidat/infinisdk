from api_object_schema import FieldBinding

class Infinipy2Binding(FieldBinding):
    def get_api_value_from_object(self, obj):
        return obj.get_field(self._field.name)

    def set_object_value_from_api(self, obj, api_value):
        obj.update_field(self._field.name, api_value)

