from api_object_schema import FieldBinding

class Infinipy2Binding(FieldBinding):
    def get_api_value_from_object(self, obj):
        """
        returns the value of the object's field
        """
        return obj.get_field(self._field.name)

    def set_object_value_from_api(self, obj, value):
        """
        update the object's field with value
        """
        obj.update_field(self._field.name, self.get_raw_api_value(value))

    def get_raw_api_value(self, value):
        """
        returns the raw value which will be sent to the remote API
        """
        return value

class ObjectIdBinding(Infinipy2Binding):
    def __init__(self, ref_collection_name=None):
        super(ObjectIdBinding, self).__init__()
        self._ref_collection_name = ref_collection_name

    def _get_ref_collection(self, collection):
        if self._ref_collection_name is not None:
            return getattr(collection, self._ref_collection_name)
        # Example: for field.name = "pool", collection will be system.pools
        return getattr(collection, self._field.name + "s")

    def get_api_value_from_object(self, obj):
        return self._get_ref_collection(obj.system.objects).get_by_id_lazy(obj.get_field(self._field.name))

    def get_raw_api_value(self, object):
        return object.id
