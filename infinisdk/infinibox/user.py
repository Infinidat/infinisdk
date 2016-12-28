from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate


class User(SystemObject):

    FIELDS = [
        Field("id", type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field("type"),
        Field("role", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default="PoolAdmin"), # For backwards compatibility
        Field("roles", type=list, mutable=True),
        Field("email", creation_parameter=True, mutable=True, default=Autogenerate("user_{uuid}@infinidat.com")),
        Field("name", creation_parameter=True, mutable=True, is_filterable=True, is_sortable=True,
              default=Autogenerate("user_{uuid}")),
        Field("password", creation_parameter=True, add_getter=False, mutable=True, default="12345678"),
        Field("enabled", type=bool, mutable=True, feature_name='user_disabling')
    ]


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

    def is_builtin(self):
        return self.get_id() < 0
