from ..core import Events as EventsBase
from ..core import Field, SystemObject
from ..core.config import config
from ..core.api.special_values import Autogenerate

_events_config = config.get_path('izbox.defaults.events')

default_event_page_size = _events_config['page_size']
default_max_events = _events_config['max_events']
max_events_page_size = _events_config['max_page_size']


class Events(EventsBase):

    def create_custom_event(self,
                            level='INFO',
                            description='custom event description',
                            visibility='CUSTOMER',
                            data=None):

        _data = {"data": data or dict(),
                 "level": level,
                 "description": description,
                 "visibility":visibility}
        return self.system.api.post("events/custom", data=_data).get_result()

    def get_event_by_uuid(self, uuid):
        result = list(self.find(uuid=uuid))
        if result:
            return result[0]

    def get_codes_list(self):
        return [e['code'] for e in self.get_codes()]

    def get_codes_description_list(self):
        return [e['description'] for e in self.get_codes()]


class PushRule(SystemObject):

    URL_PATH = "/api/rest/events/push_rules"

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("visibility", creation_parameter=True, mutable=True, default="CUSTOMER"),
        Field("filters", creation_parameter=True, mutable=True, default=list, type=list),
        Field("recipients", creation_parameter=True, mutable=True, default=list, type=list),
        Field("name", creation_parameter=True, mutable=True, default=Autogenerate("rule_{timestamp}")),
    ]
