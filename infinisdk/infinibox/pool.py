from capacity import TB
from ..core.type_binder import TypeBinder
from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject
from ..core.bindings import ListOfRelatedObjectIDsBinding, InfiniSDKBindingWithSpecialFlags
from ..core.object_query import ObjectQuery
from ..core.utils import deprecated

from urlobject import URLObject


class PoolBinder(TypeBinder):
    """Implements *system.pools*
    """

    def get_administered_pools(self):
        """Returns the pools that can be managed by the current user
        """
        return ObjectQuery(self.system, URLObject('/api/rest/pools/administered_pools'), Pool)


class Pool(InfiniBoxObject):

    BINDER_CLASS = PoolBinder

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("pool_{uuid}")),
        Field("virtual_capacity",  creation_parameter=True, mutable=True, default=TB, type=CapacityType, is_filterable=True, is_sortable=True),
        Field("physical_capacity", creation_parameter=True, mutable=True, default=TB, type=CapacityType, is_filterable=True, is_sortable=True),
        Field("owners", mutable=True, type=list, add_updater=False, binding=ListOfRelatedObjectIDsBinding('users')),
        Field("allocated_physical_capacity", api_name="allocated_physical_space", type=CapacityType),
        Field("free_physical_capacity", api_name="free_physical_space", type=CapacityType),
        Field("free_virtual_capacity", api_name="free_virtual_space", type=CapacityType),
        Field("reserved_capacity", type=CapacityType),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("ssd_enabled", type=bool, mutable=True, creation_parameter=True, is_filterable=True, is_sortable=True, optional=True),
        Field("compression_enabled", type=bool, mutable=True, feature_name='compression', add_updater=False),
        Field("max_extend", type=CapacityType, mutable=True, binding=InfiniSDKBindingWithSpecialFlags([0, -1])),
        Field("state", cached=False),
    ]

    def get_volumes(self, **kwargs):
        return self.system.volumes.find(pool_id=self.id, **kwargs)

    def get_filesystems(self, **kwargs):
        return self.system.filesystems.find(pool_id=self.id, **kwargs)

    def _get_pool_owners_url(self, owner_id=None):
        url = self.get_this_url_path().add_path('owners')
        if owner_id:
            url = url.add_path(str(owner_id))
        return url

    def set_owners(self, users):
        """sets the owners of this pool, replacing previous owners
        """
        self.update_field('owners', users)

    def is_locked(self, *args, **kwargs):
        return self.get_state(*args, **kwargs) == 'LOCKED'

    def is_limited(self, *args, **kwargs):
        return self.get_state(*args, **kwargs) == 'LIMITED'

    def lock(self):
        self.system.api.post(self.get_this_url_path().add_path('lock'))

    def unlock(self):
        self.system.api.post(self.get_this_url_path().add_path('unlock'))

    def _is_over_threshold(self, threshold):
        return (self.get_allocated_physical_capacity() * 100) >= (self.get_physical_capacity() * threshold)

    def is_over_warning_threshold(self):
        warning_threshold = self.get_field('physical_capacity_warning')
        return self._is_over_threshold(warning_threshold)

    def is_over_critical_threshold(self):
        critical_threshold = self.get_field('physical_capacity_critical')
        return self._is_over_threshold(critical_threshold)

    def enable_compression(self):
        self.update_field("compression_enabled", True)

    def disable_compression(self):
        self.update_field("compression_enabled", False)
