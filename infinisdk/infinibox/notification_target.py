from urlobject import URLObject as URL
from ..core import Field, SystemObject

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

        #### SNMP ####
        Field('version', type=str, mutable=True),
        Field('auth_protocol', mutable=True),
        Field('auth_type', mutable=True),
        Field('community', mutable=True),
        Field('engine', mutable=True),
        Field('private_key', mutable=True),
        Field('private_protocol', mutable=True),

        #### Syslog ####
        Field('transport', mutable=True),
        Field('facility', mutable=True),
    ]

    @classmethod
    def get_plural_name(cls):
        return 'notification_targets'

    def test(self, recipients=None):
        """Tests the SMTP gateway, by sending a test email to one or several recipients

        :param recipients: Either a single email or a list of emails to send to (only for SMTP)
        """
        data = {}
        if recipients is not None:
            if not isinstance(recipients, list):
                recipients = [recipients]
            data['recipients'] = recipients
        return self.system.api.post('notifications/targets/{0}/test'.format(self.id), data=data)
