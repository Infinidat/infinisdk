from ..core import SystemObject, Field
from ..core.bindings import RelatedObjectBinding, InitiatorAddressBinding, InitiatorTargetsBinding
from ..core.type_binder import TypeBinder


class InitiatorBinder(TypeBinder):
    def get_by_address(self, address):
        initiator = self.get_by_id_lazy(str(address))
        initiator.get_fields()
        return initiator


class Initiator(SystemObject):
    BINDER_CLASS = InitiatorBinder

    FIELDS = [
        Field("id", api_name="address", is_identity=True),
        Field("address", binding=InitiatorAddressBinding()),
        Field("targets", type=list, binding=InitiatorTargetsBinding()),
        Field("type"),
        Field("host", api_name="host_id", is_filterable=True, is_sortable=True, binding=RelatedObjectBinding('hosts')),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_initiators()
