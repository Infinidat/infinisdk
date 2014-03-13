from ..core import Field, SystemObject
from ..core.api.special_values import Autogenerate
from ..core.exceptions import CommandNotApproved


class User(SystemObject):

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("role", creation_parameter=True, mutable=True, default="Admin"),
        Field("email", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}@infinidat.com")),
        Field("name", api_name="username", creation_parameter=True, mutable=True, default=Autogenerate("user_{timestamp}")),
        Field("password", creation_parameter=True, add_getter=False, mutable=True, default="12345678"),
    ]

    def get_pools(self):
        pools_url = "{0}/pools".format(self.get_this_url_path())
        resp = self.system.api.get(pools_url)
        return [self.system.pools.get_by_id(pool_info['id'])
                for pool_info in resp.get_result()]

    def reset_password(self):
        url = "{0}/reset_password".format(self.get_this_url_path())
        self.system.api.put(url)

    def is_in_system(self):
        #FIXME: Remove this function when INFINIBOX-7647 will be fixed...
        # The Bug: InfiniBox returns FORBIDDEN status_code instead of not exists
        try:
            return super(User, self).is_in_system()
        except CommandNotApproved as e:
            if e.response.get_error().get('code') == 'BAD_USER':
                return False
            raise
