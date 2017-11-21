import gossip
from mitba import cached_method

from ..core import Field, CapacityType
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
        return TreeQ.create(self.system, self, *args, **kwargs)

    def get_url_path(self):
        return self._filesystem.get_this_url_path().add_path('treeqs')


class TreeQ(SystemObject):
    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("treeq_{uuid}")),
        Field("path", creation_parameter=True, is_filterable=True, is_sortable=True),
        Field("filesystem", api_name="filesystem_id", cached=True, type=int, binding=RelatedObjectBinding()),
        Field("soft_capacity", type=CapacityType, mutable=True, is_filterable=True, is_sortable=True),
        Field("soft_inodes", type=int, mutable=True, is_filterable=True, is_sortable=True),
        Field("hard_capacity", type=CapacityType, mutable=True, is_filterable=True, is_sortable=True),
        Field("hard_inodes", type=int, mutable=True, is_filterable=True, is_sortable=True),
        Field("used_capacity", type=CapacityType, is_filterable=True, is_sortable=True),
        Field("used_inodes", type=int, is_filterable=True, is_sortable=True),
        Field("capacity_state", is_filterable=True, is_sortable=True),
        Field("inodes_state", is_filterable=True, is_sortable=True),
        Field("mode", type=str, creation_parameter=True, optional=True, hidden=True)
    ]

    BINDER_CLASS = TreeQBinder

    def __init__(self, system, initial_data):
        super(TreeQ, self).__init__(system, initial_data)
        self._binder = system.filesystems.get_treeq_binder_by_id(
            initial_data.get('filesystem_id'))

    @classmethod
    def create(cls, system, binder, **fields): # pylint: disable=arguments-differ
        hook_tags = cls.get_tags_for_object_operations(system)
        gossip.trigger_with_tags('infinidat.sdk.pre_creation_data_validation',
                                 {'fields': fields, 'system': system, 'cls': cls},
                                 tags=hook_tags)
        data = get_data_for_object_creation(cls, system, fields)
        url = binder.get_url_path()
        return cls._create(system, url, data)

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