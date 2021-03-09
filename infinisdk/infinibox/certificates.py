from pathlib import Path
from urlobject import URLObject as URL

from ..core.object_query import LazyQuery
from ..core.exceptions import BadFilepathException


class Certificates:
    def __init__(self, system):
        self.system = system
        self._url_path = URL('system/certificates')

    def get_certificates(self):
        return LazyQuery(self.system, self._url_path)

    def generate_self_signed(self, dn_params=None):
        return self.system.api.post(self._url_path.add_path('generate_csr'), data=dn_params).get_result()

    def upload_csr(self, csr_path):
        return self._upload_file(self._url_path.add_path('upload_csr'), csr_path)

    def upload_pem(self, pem_path):
        return self._upload_file(self._url_path, pem_path)

    def _upload_file(self, url, file_path):
        full_file_path = _validate_file_path(file_path)
        with open(full_file_path, 'rb') as file_handler:
            return self.system.api.post(url, files={'upload_file': file_handler}).get_result()


def _validate_file_path(cert_path):
    full_path = Path(cert_path).expanduser()
    if not full_path.is_file():
        raise BadFilepathException("Invalid file path: {}".format(cert_path))
    return full_path
