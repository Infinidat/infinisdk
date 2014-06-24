###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
### 
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
### 
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
### 
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
from ..core import Events as EventsBase
from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate


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

    def get_levels(self):
        sorted_levels = sorted(self._get_events_types()['levels'], key=lambda d: d['value'])
        return [level_info['name'] for level_info in sorted_levels]


class EmailRule(SystemObject):

    URL_PATH = "/api/rest/events/mail"

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("visibility", creation_parameter=True, default="CUSTOMER", is_filterable=True, is_sortable=True),
        Field("filters", creation_parameter=True, type=list, default=list),
        Field("recipients", creation_parameter=True, type=list, default=["a@a.com"]),
        Field("name", creation_parameter=True, default=Autogenerate("rule_{timestamp}"), is_filterable=True, is_sortable=True),
    ]
