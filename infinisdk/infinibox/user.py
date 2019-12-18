from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate
from urlobject import URLObject


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
        Field("password_digest_version", type=int, is_filterable=True, is_sortable=True,
              feature_name="local_users_auth"),
        Field("is_digest_sufficient", type=bool, feature_name="fips"),
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

    def _get_reset_password_path(self):
        return URLObject(self.get_url_path(system=self.system)).add_path(self.get_name()).add_path('reset_password')

    def reset_password(self, token):
        url = self._get_reset_password_path().add_path(token)
        self.system.api.get(url)

    def request_reset_password(self):
        self.system.api.post(self._get_reset_password_path())

    def is_builtin(self):
        return self.get_id() < 0
