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


class LDAPConfigBinder(TypeBinder):

    def define(self, *args, **kwargs):
        """Alias for :func:`.create`
        """
        return self.create(*args, **kwargs)

    def set_order(self, configs):
        """Reorders LDAP configurations' priorities
        """
        self.system.api.post('config/ldap/set_order', data=[
            cfg.id for cfg in configs
            ])


class LDAPConfig(SystemObject):

    BINDER_CLASS = LDAPConfigBinder

    URL_PATH = URL('/api/rest/config/ldap')

    FIELDS = [
        Field('id', type=int, is_identity=True),
        Field('name', mutable=True),
    ]

    @classmethod
    def get_plural_name(self):
        return 'ldap_configs'

    def create_group(self, name, dn, role):
        """Maps a specified group in the LDAP directory to a specified role in the system
        """
        returned = self.system.api.post(
            'users',
            data={'name': name, 'dn': dn, 'ldap_id': self.id, 'role': role, 'type': 'Ldap'})
        return User(self.system, returned.get_result())

    def modify(self, **kwargs):
        """Modifies the LDAP configuration
        """
        post_dict = {}
        for key, value in iteritems(kwargs):
            if key.startswith('schema_'):
                post_dict.setdefault('schema_definition', {})[key.split('_', 1)[1]] = value
            else:
                post_dict[key] = value
        self.system.api.put('config/ldap/{0}'.format(self.id), data=post_dict)


    def test(self):
        """Tests the LDAP configuration
        """
        self.system.api.post('config/ldap/{0}/test'.format(self.id), data={})

    @deprecated("Use create_group instead")
    def create_local_group(self, name, role, dn):
        returned = self.system.api.post('users', data={
            'type': 'Ldap',
            'name': name,
            'roles': [
                role,
                ],
            'dn': dn,
            'ldap_id': self.id,
            })
        return self.system.users.get_by_id_lazy(returned.get_json()['result']['id'])
