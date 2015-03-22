import packaging.version

from .._compat import httplib
from ..core.config import config


class Compatability(object):
    def __init__(self, system):
        self.system = system
        self._features = None

    def can_run_on_system(self):
        system_version = self.system.get_version()
        supported_versions = config.root.infinibox.compatible_versions
        return any(version_compatibility.matches(system_version) for version_compatibility in supported_versions)

    def normalize_version_string(self, version):
        return packaging.version.parse(version)

    def get_parsed_system_version(self):
        return self.normalize_version_string(self.system.get_version())

    def get_version_major(self):
        return self.system.get_version().partition('.')[0]

    def _init_fetatures(self):
        resp = self.system.api.get("_features", assert_success=False)
        if resp.response.status_code == httplib.NOT_FOUND:
            features_list = []  # Backwards compatible
        else:
            resp.assert_success()
            features_list = resp.get_result()
        self._features = set(feature_info['name'] for feature_info in features_list)

    def _has_feature(self, feature_key):
        if self._features is None:
            self._init_fetatures()
        return feature_key in self._features

    def set_feature_as_supported(self, feature_key):
        if not self._has_feature(feature_key):
            self._features.add(feature_key)

    def has_npiv(self):
        return self._has_feature("fc/soft_targets")

    def has_replication(self):
        return int(self.get_version_major()) >= 2

    def has_nas(self):
        return self._has_feature('nas')

    def has_network_configuration(self):
        return int(self.get_version_major()) >= 2
