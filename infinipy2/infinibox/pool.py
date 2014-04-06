from capacity import TB
from ..core import Field, CapacityType
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject


class Pool(InfiniBoxObject):
    FIELDS = [
        Field("id", is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("pool_{uuid}")),
        Field("virtual_capacity",  creation_parameter=True, mutable=True, default=TB, type=CapacityType, is_filterable=True, is_sortable=True),
        Field("physical_capacity", creation_parameter=True, mutable=True, default=TB, type=CapacityType, is_filterable=True, is_sortable=True),
    ]

    def get_volumes(self):
        return self.system.volumes.find(pool_id=self.id)

    def _get_pool_owners_url(self, owner_id=None):
        url = self.get_this_url_path().add_path('owners')
        if owner_id:
            url = url.add_path(str(owner_id))
        return url

    def add_owner(self, user):
        self.system.api.post(self._get_pool_owners_url(user.id), data={})

    def discard_owner(self, user):
        self.system.api.delete(self._get_pool_owners_url(user.id), data={})
