from infinisdk.core.exceptions import APICommandFailed
import http.client as httplib

from ..core.system_object import SystemObject
from ..core import Field, CapacityType
from ..core.bindings import RelatedObjectBinding, RelatedObjectNamedBinding


class Vvol(SystemObject):

    FIELDS = [
        Field("id", type=int, cached=True, is_identity=True, is_filterable=True, is_sortable=True),
        Field("uuid", cached=True, is_filterable=True, is_sortable=True),
        Field("vvol_type", cached=True, is_filterable=True, is_sortable=True),
        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("size", is_filterable=True, is_sortable=True, type=CapacityType),
        Field("provisioning", api_name="prov_type", is_filterable=True, is_sortable=True),
        Field("pool", type='infinisdk.infinibox.pool:Pool', api_name="pool_id",
              is_filterable=True, is_sortable=True, binding=RelatedObjectNamedBinding()),
        Field("vm", type='infinisdk.infinibox.vm:Vm', api_name="vm_id",
              is_filterable=True, is_sortable=True, binding=RelatedObjectNamedBinding()),
        Field("vm_uuid", cached=True, is_filterable=True, is_sortable=True),
        Field("parent", type='infinisdk.infinibox.vvol:Vvol', cached=True, api_name="parent_id",
              binding=RelatedObjectBinding('vvols'), is_filterable=True),
        Field("name", cached=True, is_filterable=True, is_sortable=True),
        Field("guest_os", cached=True, is_filterable=True, is_sortable=True),
        Field("tree_allocated", type=CapacityType),
        Field("compression_suppressed", type=bool, feature_name="compression"),
        Field("compression_enabled", type=bool, mutable=True, creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True, feature_name="compression", toggle_name="compression"),
        Field("ssd_enabled", type=bool, mutable=True, creation_parameter=True,
              is_filterable=True, is_sortable=True, optional=True, toggle_name="ssd"),
        Field("capacity_savings", type=CapacityType, feature_name="compression"),
        Field("used_size", api_name="used", type=CapacityType),
        Field("allocated", type=CapacityType, is_filterable=True, is_sortable=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_vvol()

    def _get_fields_query(self):
        return self.get_url_path(self.system).add_query_params(dict(id=self.id, include_space_stats=True))

    def _get_fields_result(self, response):
        result = response.get_result()
        return {} if result == [] else result[0]

    def get_pool_name(self):
        return self.get_pool().get_name()

    def is_in_system(self):
        """
        Returns whether or not the vvol object actually exists in system
        """
        try:
            query = self.get_this_url_path().add_query_param("fields", ",".join('id'))
            self.system.api.get(query)
        except APICommandFailed as e:
            if e.status_code != httplib.NOT_FOUND:
                raise
            return False
        else:
            return True
