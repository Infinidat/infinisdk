from capacity import Capacity
from urlobject import URLObject as URL

from ..core.exceptions import CapacityUnavailable
from ..core.translators_and_types import CapacityTranslator

CAPACITY_SUFFIX = ["space", "capacity", "bytes"]
_python_name_to_api = {
    "free_physical_capacity": "free_physical_space",
    "free_virtual_capacity": "free_virtual_space",
}


class SystemCapacityTranslator(CapacityTranslator):
    def _from_api(self, value):
        if value is None:
            raise CapacityUnavailable()
        return super(SystemCapacityTranslator, self)._from_api(value)


class InfiniBoxSystemCapacity:
    URL_PATH = URL("/api/rest/system/capacity")

    def __init__(self, system):
        self.system = system
        self.capacity_translator = SystemCapacityTranslator()

    def _get_field(self, field_name):
        query = self.URL_PATH
        query = query.add_query_param("fields", field_name)
        response = self.system.api.get(query)
        result = response.get_result()
        return result.get(field_name, None)

    def get_fields(self, field_names=()):
        field_names = [_python_name_to_api.get(field, field) for field in field_names]
        query = self.URL_PATH
        if field_names:
            query = query.add_query_param("fields", ",".join(field_names))
        response = self.system.api.get(query)
        result = response.get_result()
        translated_result = {}
        for key, value in result.items():
            if any(key.endswith(s) for s in CAPACITY_SUFFIX):
                translated_result[key] = self.capacity_translator.from_api(value)
            else:
                translated_result[key] = value

        return translated_result

    def get_field(self, field_name):
        field_name = _python_name_to_api.get(field_name, field_name)
        return self.get_fields([field_name])[field_name]

    def _get_capacity_field(self, field_name):
        value = self._get_field(field_name)
        return self.capacity_translator.from_api(value)

    def get_id(self):
        return self._get_field("id")

    def get_free_physical_capacity(self):
        return self._get_capacity_field("free_physical_space")

    def get_free_virtual_capacity(self):
        return self._get_capacity_field("free_virtual_space")

    def get_total_physical_capacity(self):
        return self._get_capacity_field("total_physical_capacity")

    def get_total_virtual_capacity(self):
        return self._get_capacity_field("total_virtual_capacity")

    def get_total_allocated_physical_capacity(self):
        return self._get_capacity_field("total_allocated_physical_space")

    def get_allocated_physical_capacity_within_pools(self):
        return self._get_capacity_field("allocated_physical_space_within_pools")

    def get_allocated_virtual_capacity_within_pools(self):
        return self._get_capacity_field("allocated_virtual_space_within_pools")

    def get_dynamic_spare_drive_cost(self):
        return self._get_field("dynamic_spare_drive_cost")

    def get_used_dynamic_spare_partitions(self):
        return self._get_field("used_dynamic_spare_partitions")

    def get_used_dynamic_spare_capacity(self):
        return self._get_capacity_field("used_dynamic_spare_bytes")

    def get_used_spare_partitions(self):
        return self._get_field("used_spare_partitions")

    def get_used_spare_capacity(self):
        return self._get_capacity_field("used_spare_bytes")

    def get_total_spare_partitions(self):
        return self._get_field("total_spare_partitions")

    def get_total_spare_capacity(self):
        return self._get_capacity_field("total_spare_bytes")

    def get_data_reduction_ratio(self):
        return self._get_field("data_reduction_ratio")

    def update_total_virtual_capacity(self, total_virtual_capacity):
        if not isinstance(total_virtual_capacity, int):
            if not isinstance(total_virtual_capacity, Capacity):
                raise ValueError("Parameter must be of type Integer or Capacity")
            total_virtual_capacity = self.capacity_translator.to_api(
                total_virtual_capacity
            )
        self.system.api.put(
            "system/capacity/total_virtual_capacity", data=total_virtual_capacity
        )
