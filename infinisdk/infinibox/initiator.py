from infinisdk.core.exceptions import APICommandFailed

from ..core import Field, SystemObject
from ..core.bindings import (
    InitiatorAddressBinding,
    InitiatorTargetsBinding,
    RelatedObjectBinding,
)
from ..core.type_binder import TypeBinder


class InitiatorBinder(TypeBinder):
    def __init__(self, object_type, system):
        """
        Since field "id" is the string version of field "address"
        We will specify "address" as being the key in all the
        get_by_id type of methods
        """

        super().__init__(object_type, system)
        self.initiator_id_field = self.object_type.fields["address"].name

    def get_by_address(self, address):
        initiator = self.get_by_id_lazy(str(address))
        initiator.get_fields()
        return initiator

    def get_by_id_lazy(self, id):  # pylint: disable=redefined-builtin
        if self._cache is not None:
            obj = self._cache.safe_get_by_id_from_cache(id)
            if obj is not None:
                return obj
        try:
            return self.object_type.construct(
                self.system, {self.object_type.UID_FIELD: id}
            )
        except KeyError:
            return self.object_type.construct(
                self.system, {self.initiator_id_field: id}
            )

    def get_by_id(self, id):  # pylint: disable=redefined-builtin
        return self.get_by_address(id)

    def safe_get_by_id(self, id):  # pylint: disable=redefined-builtin
        try:
            return self.get_by_address(id)
        except APICommandFailed:
            return None


class Initiator(SystemObject):
    BINDER_CLASS = InitiatorBinder

    FIELDS = [
        Field("id", api_name="address", is_identity=True),
        Field("address", binding=InitiatorAddressBinding()),
        Field("targets", type=list, binding=InitiatorTargetsBinding()),
        Field("type"),
        Field(
            "host",
            api_name="host_id",
            is_filterable=True,
            is_sortable=True,
            binding=RelatedObjectBinding("hosts"),
        ),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_initiators()
