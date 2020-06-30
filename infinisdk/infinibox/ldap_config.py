from urlobject import URLObject as URL

from ..core.type_binder import TypeBinder
from ..core import Field, SystemObject
from .user import User


class LDAPConfigBinder(TypeBinder):

    def define(self, *args, **kwargs):
        """Alias for :func:`.create <infinisdk.core.type_binder.MonomorphicBinder.create>`
        """
        return self.create(*args, **kwargs)

    def set_order(self, configs):
        """Reorders LDAP configurations' priorities
        """
        self.system.api.post('config/ldap/set_order', data=[
            cfg.id for cfg in configs
            ])

    def reload(self):
        self.system.api.post('config/ldap/reload')

    flush_cache = reload


class LDAPConfig(SystemObject):

    BINDER_CLASS = LDAPConfigBinder

    URL_PATH = URL('/api/rest/config/ldap')

    FIELDS = [
        Field('id', type=int, is_identity=True),
        Field('name', mutable=True),
    ]

    @classmethod
    def get_type_name(cls):
        return 'ldap_config'

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
        for key, value in kwargs.items():
            if key.startswith('schema_'):
                post_dict.setdefault('schema_definition', {})[key.split('_', 1)[1]] = value
            else:
                post_dict[key] = value
        self.system.api.put('config/ldap/{}'.format(self.id), data=post_dict)


    def test(self):
        """Tests the LDAP configuration
        """
        self.system.api.post('config/ldap/{}/test'.format(self.id), data={})
