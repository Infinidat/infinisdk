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
from ..core.utils import deprecated


class User(SystemObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("role", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default="PoolAdmin"),
        Field("email", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}@infinidat.com")),
        Field("name", api_name="username", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, default=Autogenerate("user_{timestamp}")),
        Field("password", creation_parameter=True, add_getter=False, mutable=True, default="12345678"),
    ]

    @deprecated(message='Use User.get_owned_pools or User.get_administered_pools instead')
    def get_pools(self):
        return self.get_owned_pools()

    def get_owned_pools(self):
        """Returns the pools that are owned by this user
        """
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
