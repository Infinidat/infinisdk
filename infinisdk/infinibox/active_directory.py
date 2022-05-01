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
        self, *, domain, org_unit=OMIT, preferred_ips, username, password, tenant=None
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
        :returns: Dictionary with fields: "tenant_id", "domain", "org_unit", "preferred_ips"
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
            },
        ).get_result()

    @classmethod
    def get_type_name(cls):
        return "active_directory_domain"

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_native_smb()
