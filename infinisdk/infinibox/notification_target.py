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
from urlobject import URLObject as URL

from .._compat import iteritems
from ..core.type_binder import TypeBinder
from ..core import Field, SystemObject
from ..core.utils import deprecated
from .user import User



class NotificationTarget(SystemObject):


    URL_PATH = URL('/api/rest/notifications/targets')

    FIELDS = [
        Field('id', type=int, is_identity=True),
        Field('name', mutable=True),
        Field('protocol'),

        #### SMTP #####
        Field('tls', type=bool, mutable=True),
        Field('host', mutable=True),
        Field('port', type=int, mutable=True),
        Field('from_address', mutable=True),
        Field('username', mutable=True),
        Field('password', mutable=True),
    ]

    @classmethod
    def get_plural_name(cls):
        return 'notification_targets'

    def test(self, recipients):
        """Tests the SMTP gateway, by sending a test email to one or several recipients

        :param recipients: Either a single email or a list of emails to send to
        """
        if not isinstance(recipients, list):
            recipients = [recipients]
        return self.system.api.post('notifications/targets/{0}/test'.format(self.id),
                                    data={'recipients': recipients})
