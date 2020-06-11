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
        return response.get_result()[0]
