from urlobject import URLObject as URL

from ..core import Field
from ..core.bindings import RelatedObjectBinding, RelatedComponentBinding
from ..core.system_object import SystemObject
from ..core.system_object_utils import get_data_for_object_creation
from ..core.translators_and_types import WWNType
from ..core.type_binder import TypeBinder


class FcSoftTargetsBinder(TypeBinder):

    def create_many(self, **fields):
        '''
        Creates multiple soft targets in single API command.
        :param fields: All :class:`.FcSoftTarget` creation parameters & quantity
        :returns: a list of :class:`.FcSoftTarget` objects
        '''
        url = self.get_url_path().add_path('create_multiple')
        data = get_data_for_object_creation(self.object_type, self.system, fields)
        res = self.system.api.post(url, data=data)
        return [self.object_type.construct(self.system, obj_info)
                for obj_info in res.get_result()]

    def redistribute(self):
        url = self.get_url_path().add_path('redistribute')
        return self.system.api.post(url, data={})

    def wipe(self):
        url = self.get_url_path().add_path('wipe')
        return self.system.api.post(url, data={})


class FcSoftTarget(SystemObject):

    BINDER_CLASS = FcSoftTargetsBinder
    URL_PATH = URL('fc/soft_targets')

    FIELDS = [
        Field("id", type=int, is_identity=True, cached=True),
        Field("wwpn", cached=True, type=WWNType),
        Field("port_number", type=int),
        Field("switch", api_name="switch_id", type="infinisdk.infinibox.fc_switch:FcSwitch",
              creation_parameter=True, binding=RelatedObjectBinding('fc_switches')),
        Field("node", api_name="node_id",
              binding=RelatedComponentBinding(api_index_name='node_id', value_for_none=None)),
        Field("is_home", type=bool, add_getter=False),
    ]

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_npiv()

    @classmethod
    def get_type_name(cls):
        return "fc_soft_target"

    def is_home(self, **kwargs):
        return self.get_field('is_home', **kwargs)
