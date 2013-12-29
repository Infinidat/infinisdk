from ..core import Events as EventsBase


class Events(EventsBase):

    def create_custom_event(self,
                            level='INFO',
                            description='custom event',
                            visibility='INFINIDAT',
                            data=None):

        _data = {"data": data or [],
                 "level": level,
                 "description_template": description,
                 "visibility":visibility}
        return self.system.api.post("events/custom", data=_data).get_result()
