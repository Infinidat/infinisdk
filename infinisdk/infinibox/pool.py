from capacity import TB
from sentinels import NOTHING
from ..core.type_binder import TypeBinder
from ..core import Field, CapacityType, MillisecondsDatetimeType
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject
from ..core.bindings import ListOfRelatedObjectIDsBinding, InfiniSDKBindingWithSpecialFlags
from ..core.object_query import ObjectQuery

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
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("pool_{uuid}")),
        Field("virtual_capacity", creation_parameter=True, mutable=True, default=TB, type=CapacityType,
              is_filterable=True, is_sortable=True),
        Field("physical_capacity", creation_parameter=True, mutable=True, default=TB, type=CapacityType,
              is_filterable=True, is_sortable=True),
        Field("owners", mutable=True, type=list, add_updater=False, binding=ListOfRelatedObjectIDsBinding('users')),
        Field("allocated_physical_capacity", api_name="allocated_physical_space", type=CapacityType),
        Field("free_physical_capacity", api_name="free_physical_space", type=CapacityType),
        Field("free_virtual_capacity", api_name="free_virtual_space", type=CapacityType),
        Field("physical_capacity_critical", type=int, creation_parameter=True, optional=True, mutable=True),
        Field("physical_capacity_warning", type=int, creation_parameter=True, optional=True, mutable=True),
        Field("reserved_capacity", type=CapacityType),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("ssd_enabled", type=bool, mutable=True, creation_parameter=True, is_filterable=True, is_sortable=True,
              optional=True, toggle_name='ssd'),
        Field("compression_enabled", type=bool, mutable=True, feature_name='compression', toggle_name='compression',
              is_filterable=True, is_sortable=True),
        Field("capacity_savings", type=CapacityType, feature_name='compression'),
        Field("max_extend", type=CapacityType, mutable=True, creation_parameter=True, optional=True,
              binding=InfiniSDKBindingWithSpecialFlags([-1])),
        Field("state", cached=False),
        Field("volumes_count", type=int),
        Field("snapshots_count", type=int),
        Field("filesystems_count", type=int),
        Field("filesystem_snapshots_count", type=int),
        Field("entities_count", type=int),
    ]

    @classmethod
    def create(cls, system, **fields):
        capacity = fields.pop('capacity', NOTHING)
        if capacity is not NOTHING:
            for field_name in ['virtual_capacity', 'physical_capacity']:
                assert field_name not in fields
                fields[field_name] = capacity
        return super(Pool, cls).create(system, **fields)

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
        # pylint: disable=no-member
        return self.get_state(*args, **kwargs) == 'LOCKED'

    def is_limited(self, *args, **kwargs):
        # pylint: disable=no-member
        return self.get_state(*args, **kwargs) == 'LIMITED'

    def lock(self):
        self.system.api.post(self.get_this_url_path().add_path('lock'))

    def unlock(self):
        self.system.api.post(self.get_this_url_path().add_path('unlock'))

    def _is_over_threshold(self, threshold):
        # pylint: disable=no-member
        return (self.get_allocated_physical_capacity() * 100) >= (self.get_physical_capacity() * threshold)

    def is_over_warning_threshold(self):
        warning_threshold = self.get_field('physical_capacity_warning')
        return self._is_over_threshold(warning_threshold)

    def is_over_critical_threshold(self):
        critical_threshold = self.get_field('physical_capacity_critical')
        return self._is_over_threshold(critical_threshold)
