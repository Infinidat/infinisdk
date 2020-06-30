from urlobject import URLObject as URL
import os
from ..core.exceptions import BadFilepathException

class Kms:
    def __init__(self, system):
        self.system = system
        self._url_path = URL('system/kms')

    def get_config(self):
        return self.system.api.get(self._url_path).get_result()

    def set_config(self, new_config):
        return self.system.api.put(self._url_path.add_path('set_configuration'), data=new_config).get_result()

    def _validate_filepath(self, filepath):
        fullpath = os.path.expanduser(filepath)
        if not os.path.isfile(fullpath):
            raise BadFilepathException()
        return fullpath

    def upload_kms_ca_certificate(self, filepath):
        filepath = self._validate_filepath(filepath)
        with open(filepath, 'rb') as f:
            self.system.api.post(self._url_path.add_path('upload_kms_ca_certificate'), files={'upload_file': f})

    def upload_infinibox_certificate_and_key(self, filepath):
        filepath = self._validate_filepath(filepath)
        with open(filepath, 'rb') as f:
            self.system.api.post(self._url_path.add_path('upload_infinibox_certificate_and_key'),
                                 files={'upload_file': f})

    def enable(self):
        self.system.api.post('system/kms_enable')

    def disable(self):
        self.system.api.post('system/kms_disable')

    def is_enabled(self):
        return self.system.api.get('config/security/is_kms_enabled').get_result()

    def get_connectivity_state(self, **kwargs):
        return self.system.components.system_component.get_field('security', **kwargs)['kmip_connectivity_state']

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_kms()
