from urlobject import URLObject as URL
from capacity import Capacity
from ..core.exceptions import CapacityUnavailable
from .._compat import integer_types
from ..core.translators_and_types import CapacityTranslator


class SystemCapacityTranslator(CapacityTranslator):
    def _from_api(self, value):
        if value is None:
            raise CapacityUnavailable()
        return super(SystemCapacityTranslator, self)._from_api(value)


class InfiniBoxSystemCapacity(object):
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

    def _get_capacity_field(self, field_name):
        value = self._get_field(field_name)
        return self.capacity_translator.from_api(value)

    def get_id(self):
        return self._get_field('id')

    def get_free_physical_capacity(self):
        return self._get_capacity_field('free_physical_space')

    def get_free_virtual_capacity(self):
        return self._get_capacity_field('free_virtual_space')

    def get_total_physical_capacity(self):
        return self._get_capacity_field('total_physical_capacity')

    def get_total_virtual_capacity(self):
        return self._get_capacity_field('total_virtual_capacity')

    def update_total_virtual_capacity(self, total_virtual_capacity):
        if not isinstance(total_virtual_capacity, integer_types):
            if not isinstance(total_virtual_capacity, Capacity):
                raise ValueError('Parameter must be of type Integer or Capacity')
            total_virtual_capacity = self.capacity_translator.to_api(total_virtual_capacity)
        self.system.api.put('system/capacity/total_virtual_capacity', data=total_virtual_capacity)
