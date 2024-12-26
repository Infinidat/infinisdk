from urlobject import URLObject as URL

from ..core.api.special_values import OMIT


class ActiveDirectoryDomains:
    def __init__(self, system):
        self.system = system
        self._url_path = "activedirectory/domains"

    def get(self):
        """Obtains the active directory domain

        :returns: Dictionary with fields: "tenant_id", "domain", "org_unit", "preferred_ips"
        :rtype: dict
        """
        return self.system.api.get(
            self._url_path,
        ).get_result()

    def leave(
        self,
        *,
        username,
        password,
    ):
        """Leave the active directory domain

        :param username: the username for the domain
        :type username: str
        :param password: the password for the domain
        :type password: str
        """
        return self.system.api.post(
            self._url_path + "/leave", data={"username": username, "password": password}
        ).get_result()

    def create(
        self,
        *,
        domain,
        org_unit=OMIT,
        preferred_ips,
        username,
        password,
        tenant=None,
        unix_services_enabled=OMIT,
        uid_attribute_name=OMIT,
        gid_attribute_name=OMIT,
        max_translated_groups=OMIT,
    ):
        """Join an active directory domain

        :param domain: the domain to join
        :type domain: str
        :param org_unit: the organization unit
        :type org_unit: str
        :param preferred_ips: a list of ips
        :type preferred_ips: list[str]
        :param username: the username for the domain
        :type username: str
        :param password: the password for the domain
        :type password: str
        :param tenant: the tenant object
        :type tenant: :class:`infinisdk.infinibox.tenant.Tenant`
        :param unix_services_enabled: indicates if RFC2307 Unix Services are to be used when joined to Active Directory
        :type unix_services_enabled: bool
        :param uid_attribute_name: The name of the AD attribute that provides the numeric UID of a user principal
        :type uid_attribute_name: str
        :param gid_attribute_name: The name of the AD attribute that provides the numeric GID of a user principal
        :type gid_attribute_name: str
        :param max_translated_groups: The maximum number of groups translated per user via RFC2307 Unix Services
        :type max_translated_groups: int
        :returns: Dictionary with fields: "tenant_id", "domain", "org_unit", "preferred_ips", "unix_services_enabled", "uid_attribute_name", "gid_attribute_name", "max_translated_groups"
        :rtype: dict
        """
        return self.system.api.post(
            self._url_path,
            data={
                "domain": domain,
                "org_unit": org_unit,
                "preferred_ips": preferred_ips,
                "username": username,
                "password": password,
                "tenant_id": tenant.id if tenant is not None else OMIT,
                "unix_services_enabled": unix_services_enabled,
                "uid_attribute_name": uid_attribute_name,
                "gid_attribute_name": gid_attribute_name,
                "max_translated_groups": max_translated_groups,
            },
        ).get_result()

    join = create

    @classmethod
    def get_type_name(cls):
        return "active_directory_domain"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb()

    def set_unix_services(
        self,
        *,
        unix_services_enabled=OMIT,
        uid_attribute_name=OMIT,
        gid_attribute_name=OMIT,
        max_translated_groups=OMIT,
    ):
        """Set unix services for a domain

        :param unix_services_enabled: indicates if RFC2307 Unix Services are to be used when joined to Active Directory
        :type unix_services_enabled: bool
        :param uid_attribute_name: The name of the AD attribute that provides the numeric UID of a user principal
        :type uid_attribute_name: str
        :param gid_attribute_name: The name of the AD attribute that provides the numeric GID of a user principal
        :type gid_attribute_name: str
        :param max_translated_groups: The maximum number of groups translated per user via RFC2307 Unix Services
        :type max_translated_groups: int
        :returns: Dictionary with fields: "unix_services_enabled", "uid_attribute_name", "gid_attribute_name", "max_translated_groups"
        :rtype: dict
        """
        return self.system.api.post(
            self._url_path + "/set_unix_services",
            data={
                "unix_services_enabled": unix_services_enabled,
                "uid_attribute_name": uid_attribute_name,
                "gid_attribute_name": gid_attribute_name,
                "max_translated_groups": max_translated_groups,
            },
        ).get_result()

    def set_max_translated_groups(
        self,
        *,
        max_translated_groups,
    ):
        """Set unix services for a domain

        :param unix_services_enabled: indicates if RFC2307 Unix Services are to be used when joined to Active Directory
        :type unix_services_enabled: bool
        :param uid_attribute_name: The name of the AD attribute that provides the numeric UID of a user principal
        :type uid_attribute_name: str
        :param gid_attribute_name: The name of the AD attribute that provides the numeric GID of a user principal
        :type gid_attribute_name: str
        :param max_translated_groups: The maximum number of groups translated per user via RFC2307 Unix Services
        :type max_translated_groups: int
        :returns: Dictionary with fields: "unix_services_enabled", "uid_attribute_name", "gid_attribute_name", "max_translated_groups"
        :rtype: dict
        """
        return self.system.api.post(
            self._url_path + "/set_max_translated_groups",
            data={
                "max_translated_groups": max_translated_groups,
            },
        ).get_result()

    def query_user(self, *, sid=OMIT, uid=OMIT, username=OMIT):
        """Query for a user

        :param sid: The sid of the user
        :type sid: str
        :param uid: The uid of the user
        :type uid: str
        :param username: The username
        :type username: str
        :returns: List of users with fields: "tenant_id", "name", "username", "sid", "gsid", "uid", "gid"
        :rtype: dict
        """

        url = URL(self._url_path + "/user_query")

        if sid is not OMIT:
            url = url.add_query_param("sid", sid)
        elif uid is not OMIT:
            url = url.add_query_param("uid", uid)
        elif username is not OMIT:
            url = url.add_query_param("username", username)

        return self.system.api.get(url).get_result()
