from urlobject import URLObject as URL

from infinisdk.core.translators_and_types import MunchType

from ..core import Field, SystemObject
from ..core.type_binder import TypeBinder
from .user import User


class LDAPConfigBinder(TypeBinder):
    def define(self, *args, **kwargs):
        """Alias for :func:`.create <infinisdk.core.type_binder.TypeBinder.create>`"""
        return self.create(*args, **kwargs)

    def define_active_directory(self, *args, **kwargs):
        kwargs["repository_type"] = "ActiveDirectory"
        return self.create(*args, **kwargs)

    def define_open_ldap(self, *args, **kwargs):
        kwargs["repository_type"] = "LDAP"
        return self.create(*args, **kwargs)

    def set_order(self, configs):
        """Reorders LDAP configurations' priorities"""
        self.system.api.post("config/ldap/set_order", data=[cfg.id for cfg in configs])

    def reload(self):
        self.system.api.post("config/ldap/reload")

    flush_cache = reload


class LDAPConfig(SystemObject):

    BINDER_CLASS = LDAPConfigBinder

    URL_PATH = URL("/api/rest/config/ldap")

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field(
            "name",
            mutable=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "ldap_port",
            mutable=True,
            type=int,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "use_ldaps",
            mutable=True,
            type=bool,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "domain_name",
            creation_parameter=True,
            optional=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "bind_username",
            mutable=True,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "search_order",
            type=int,
            is_filterable=True,
            is_sortable=True,
        ),
        Field(
            "servers",
            type=list,
            creation_parameter=True,
            optional=True,
        ),
        Field(
            "repository_type",
            optional=True,
            creation_parameter=True,
        ),
        Field(
            "schema_definition",
            type=MunchType,
            mutable=True,
        ),
    ]

    @classmethod
    def get_type_name(cls):
        return "ldap_config"

    def create_group(self, name, dn, role):
        """Maps a specified group in the LDAP directory to a specified role in the system"""
        returned = self.system.api.post(
            "users",
            data={
                "name": name,
                "dn": dn,
                "ldap_id": self.id,
                "role": role,
                "type": "Ldap",
            },
        )
        return User(self.system, returned.get_result())

    def modify(self, **kwargs):
        """Modifies the LDAP configuration"""
        post_dict = {}
        for key, value in kwargs.items():
            if key.startswith("schema_"):
                post_dict.setdefault("schema_definition", {})[
                    key.split("_", 1)[1]
                ] = value
            else:
                post_dict[key] = value
        self.system.api.put("config/ldap/{}".format(self.id), data=post_dict)

    def test(self):
        """Tests the LDAP configuration"""
        self.system.api.post("config/ldap/{}/test".format(self.id), data={})
