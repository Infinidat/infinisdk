from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate


class User(SystemObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("type"),
        Field("role", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True, optional=True),
        Field("roles", creation_parameter=True, type=list, mutable=True, optional=True),
        Field("email", creation_parameter=True, mutable=True, default=Autogenerate("user_{uuid}@infinidat.com")),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("user_{uuid}")),
        Field("password", creation_parameter=True, hidden=True, mutable=True, default="12345678"),
        Field("enabled", type=bool, mutable=True, feature_name='user_disabling', creation_parameter=True,
              optional=True),
    ]

    @classmethod
    def create(cls, system, **fields):
        if 'role' not in fields and 'roles' not in fields:
            fields['role'] = 'PoolAdmin' # For backwards compatibility
        return super(User, cls).create(system, **fields)

    def get_owned_pools(self):
        """Returns the pools that are owned by this user
        """
        pools_url = "{}/pools".format(self.get_this_url_path())
        resp = self.system.api.get(pools_url)
        return [self.system.pools.get_by_id(pool_info['id'])
                for pool_info in resp.get_result()]

    def reset_password(self, token):
        url = self.get_this_url_path().add_path('reset_password').add_path(token)
        self.system.api.get(url)

    def request_reset_password(self):
        url = self.get_this_url_path().add_path('reset_password')
        self.system.api.post(url)

    def is_builtin(self):
        return self.get_id() < 0
