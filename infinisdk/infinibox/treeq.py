import gossip
from mitba import cached_method

from ..core import Field, CapacityType
from ..core.utils import end_reraise_context
from ..core.system_object_utils import get_data_for_object_creation
from ..core.api.special_values import Autogenerate
from ..core.system_object import SystemObject
from ..core.bindings import RelatedObjectBinding
from ..core.type_binder import TypeBinder


class TreeQBinder(TypeBinder):
    def __init__(self, system, filesystem):
        super(TreeQBinder, self).__init__(TreeQ, system)
        self._filesystem = filesystem

    def create(self, *args, **kwargs):
        hook_tags = TreeQ.get_tags_for_object_operations(self.system)
        hook_data = {'fields': kwargs, 'system': self.system, 'filesystem': self._filesystem}
        gossip.trigger_with_tags('infinidat.sdk.pre_treeq_creation', hook_data, tags=hook_tags)
        try:
            treeq = TreeQ.create(self.system, self, *args, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            with end_reraise_context():
                hook_data['exception'] = e
                gossip.trigger_with_tags('infinidat.sdk.treeq_creation_failure', hook_data, tags=hook_tags)
        hook_data['treeq'] = treeq
        gossip.trigger_with_tags('infinidat.sdk.post_treeq_creation', hook_data, tags=hook_tags)
        return treeq

    def get_filesystem(self):
        return self._filesystem

    def get_url_path(self):
        return self._filesystem.get_this_url_path().add_path('treeqs')

    def __repr__(self):
        return '<{}:Filesystem id={}.treeqs>'.format(
            self._filesystem.system.get_name(), self._filesystem.id)



class TreeQ(SystemObject):
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("treeq_{uuid}")),
        Field("path", creation_parameter=True, cached=True, is_filterable=True, is_sortable=True,
              default=Autogenerate('/{prefix}treeq_{uuid}')),
        Field("filesystem", api_name="filesystem_id", cached=True, type=int, binding=RelatedObjectBinding(),
              use_in_repr=True),
        Field("soft_capacity", type=CapacityType, mutable=True, creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True),
        Field("soft_inodes", type=int, mutable=True, creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True),
        Field("hard_capacity", type=CapacityType, mutable=True, creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True),
        Field("hard_inodes", type=int, mutable=True, creation_parameter=True, optional=True,
              is_filterable=True, is_sortable=True),
        Field("used_capacity", type=CapacityType, cached=False, is_filterable=True, is_sortable=True),
        Field("used_inodes", type=int, cached=False, is_filterable=True, is_sortable=True),
        Field("capacity_state", cached=False, is_filterable=True, is_sortable=True),
        Field("inodes_state", cached=False, is_filterable=True, is_sortable=True),
        Field("mode", type=str, creation_parameter=True, optional=True, hidden=True)
    ]

    BINDER_CLASS = TreeQBinder

    def __init__(self, system, initial_data):
        super(TreeQ, self).__init__(system, initial_data)
        self._binder = system.filesystems.get_treeq_binder_by_id(
            initial_data.get('filesystem_id'))

    def __eq__(self, other):
        return type(other) == type(self) and other.get_unique_key() == self.get_unique_key()  # pylint: disable=unidiomatic-typecheck

    def __hash__(self):
        return hash(self.get_unique_key())

    def get_unique_key(self):
        return (self.system, type(self).__name__, self.get_filesystem(), self.id)

    @classmethod
    def create(cls, system, binder, **fields): # pylint: disable=arguments-differ
        hook_tags = cls.get_tags_for_object_operations(system)
        gossip.trigger_with_tags('infinidat.sdk.pre_creation_data_validation',
                                 {'fields': fields, 'system': system, 'cls': cls},
                                 tags=hook_tags)
        data = get_data_for_object_creation(cls, system, fields)
        url = binder.get_url_path()
        return cls._create(system, url, data, parent=binder.get_filesystem())

    @classmethod
    def get_type_name(cls):
        return "treeq"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_treeq()

    @cached_method
    def get_this_url_path(self):
        return self.get_filesystem().get_this_url_path().add_path('treeqs').add_path(str(self.get_id()))

    def get_binder(self):
        return self._binder
