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
from ..core import SystemObject, Field
from ..core.api.special_values import Autogenerate

class User(SystemObject):

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("role", creation_parameter=True, mutable=True, default="INFINIDAT"),
        Field("email", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}@infinidat.com")),
        Field("name", api_name="username", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}")),
        Field("password", creation_parameter=True, mutable=True, default="12345678"),
    ]
