from ..core.api.special_values import OMIT


class ActiveDirectoryDomains:
    def __init__(self, system):
        self.system = system
        self._url_path = "activedirectory/domains"

    def create(
        self, *, domain, org_unit=OMIT, preferred_ips, username, password, tenant=None
    ):
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
