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
from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate
from ..core.exceptions import CommandNotApproved


class User(SystemObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("role", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default="Admin"),
        Field("email", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}@infinidat.com")),
        Field("name", api_name="username", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("user_{timestamp}")),
        Field("password", creation_parameter=True, add_getter=False, mutable=True, default="12345678"),
    ]

    def get_pools(self):
        pools_url = "{0}/pools".format(self.get_this_url_path())
        resp = self.system.api.get(pools_url)
        return [self.system.pools.get_by_id(pool_info['id'])
                for pool_info in resp.get_result()]

    def reset_password(self, token):
        url = self.get_this_url_path().add_path('reset_password').add_path(token)
        self.system.api.get(url)

    def request_reset_password(self):
        url = self.get_this_url_path().add_path('reset_password')
        self.system.api.post(url)


    def is_in_system(self):
        #FIXME: Remove this function when INFINIBOX-7647 will be fixed...
        # The Bug: InfiniBox returns FORBIDDEN status_code instead of not exists
        try:
            return super(User, self).is_in_system()
        except CommandNotApproved as e:
            if e.response.get_error().get('code') == 'BAD_USER':
                return False
            raise
