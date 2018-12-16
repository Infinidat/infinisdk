from ..core.system_object import BaseSystemObject
from ..core.type_binder import TypeBinder
from ..core.api.special_values import OMIT
from ..core.bindings import RelatedObjectNamedBinding
from ..core import Field
from urlobject import URLObject as URL

class NlmLockTypeBinder(TypeBinder):
    def break_lock(self, lock=OMIT, filesystem=OMIT, file_path=OMIT, client=OMIT):
        data = {'file_path': file_path, 'client': client}
        data['filesystem_id'] = filesystem.get_id() if filesystem is not OMIT else OMIT
        data['lock_id'] = lock.get_id() if lock is not OMIT else OMIT
        url = URL(self.object_type.get_url_path(self.system))
        res = self.system.api.post(url.add_path('break'), data=data)
        return res.get_result()

    def remove_orphan(self):
        url = URL(self.object_type.get_url_path(self.system))
        res = self.system.api.post(url.add_path('remove_orphan'))
        return res.get_result()

class NlmLock(BaseSystemObject):
    BINDER_CLASS = NlmLockTypeBinder

    @classmethod
    def get_tags_for_object_operations(cls, system):
        return [cls.get_type_name().lower(), system.get_type_name().lower()]

    @classmethod
    def get_type_name(cls):
        return 'nlm_lock'

    FIELDS = [
        Field("id", api_name='lock_id', type=str, is_identity=True, is_filterable=True, is_sortable=True),
        Field("lock_id", type=str, is_identity=True, is_filterable=True, is_sortable=True),
        Field("filesystem", type='infinisdk.infinibox.filesystem:Filesystem', api_name="filesystem_id",
              is_filterable=True, is_sortable=True, binding=RelatedObjectNamedBinding(), cached=True),
        Field("file_path", type=str, is_filterable=True, is_sortable=True, cached=True),
        Field("file_path_status", type=str, is_filterable=True, is_sortable=True),
        Field("client", type=str, is_filterable=True, is_sortable=True, cached=True),
        Field("state", type=str, is_filterable=True, is_sortable=True),
        Field("offset", type=int, cached=True),
        Field("length", type=int, cached=True),
        Field("lock_type", type=str, is_filterable=True, is_sortable=True, cached=True),
        Field("granted_at", type=int, is_filterable=True, is_sortable=True, cached=True),
        Field("owner", type=str, is_filterable=True, is_sortable=True, cached=True),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_nlm()
