from ..core import Field, MillisecondsDatetimeType
from ..core.bindings import RelatedObjectBinding
from ..core.api.special_values import Autogenerate
from .system_object import InfiniBoxObject

_CG_SUFFIX = Autogenerate('_{timestamp}')


class ConsGroup(InfiniBoxObject):
    URL_PATH = 'cgs'

    FIELDS = [
        Field("id", is_identity=True, type=int, cached=True),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("cg_{uuid}")),
        Field("type", cached=True, is_filterable=True, is_sortable=True),
        Field("pool", type='infinisdk.infinibox.pool:Pool', api_name="pool_id", creation_parameter=True,
            is_filterable=True, is_sortable=True, binding=RelatedObjectBinding()),
        Field("parent", type='infinisdk.infinibox.cons_group:ConsGroup', cached=True, api_name="parent_id",
                binding=RelatedObjectBinding('cons_groups'), is_filterable=True, is_sortable=True),
        Field("replicated", api_name="is_replicated", type=bool, is_filterable=True, is_sortable=True),
        Field("members_count", type=int, is_filterable=True, is_sortable=True),
        Field("created_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
        Field("updated_at", type=MillisecondsDatetimeType, is_sortable=True, is_filterable=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_consistency_groups()

    @classmethod
    def get_type_name(cls):
        return 'cons_group'

    def create_snapgroup(self, name=None, prefix=None, suffix=None):
        # TODO: call fork hooks for all the members...
        self.refresh('members_count')
        if not name:
            name = self.fields.name.generate_default().generate()
        if not prefix and not suffix:
            suffix = _CG_SUFFIX.generate()
        data = {'snap_prefix': prefix, 'parent_id': self.get_id(), 'snap_suffix': suffix, 'name': name}
        child = self._create(self.system, self.get_url_path(self.system), data=data, tags=None)
        return child

    def delete(self, delete_members=None):
        path = self.get_this_url_path()
        if delete_members is not None:
            path = path.add_query_param('delete_members', 'true')
        with self._get_delete_context():
            self.system.api.delete(path)

    def _get_members_url(self):
        return self.get_this_url_path().add_path('members')

    def get_members(self):
        members_info = self.system.api.get(self._get_members_url()).get_result()
        returned = []
        for member_info in members_info:
            type_name = 'volume' if member_info['dataset_type'] == 'VOLUME' else 'filesystem'
            binder = self.system.objects.get_binder_by_type_name(type_name)
            returned.append(binder.object_type(self.system, member_info))
        return returned

    def add_member(self, member, **kwargs):
        data = kwargs
        data['dataset_id'] = member.id
        self.system.api.post(self._get_members_url(), data=data)
        self.refresh('members_count')

    def remove_member(self, member):
        self.system.api.delete(self._get_members_url().add_path(str(member.id)))
        self.refresh('members_count')

    def restore(self, snap_group):
        raise NotImplementedError()

    def move_pool(self, target_pool, with_capacity=False):
        """Moves this entity to a new pool, optionally along with its needed capacity
        """
        data = dict(pool_id=target_pool.get_id(), with_capacity=with_capacity)
        self.system.api.post(self.get_this_url_path().add_path('move'), data=data)
        self.refresh('pool')
