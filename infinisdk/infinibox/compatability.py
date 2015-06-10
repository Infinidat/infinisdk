###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2014, 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
import packaging.version
from sentinels import NOTHING

from packaging.version import parse as parse_version

from .._compat import httplib
from ..core.config import config


class Compatability(object):
    def __init__(self, system):
        self.system = system
        self._features = None

    def can_run_on_system(self):
        version_string = self.system.get_version().split('-', 1)[0]
        system_version = self.normalize_version_string(version_string)
        supported_versions = config.root.infinibox.compatible_versions
        return any(v.contains(system_version) for v in supported_versions)

    def normalize_version_string(self, version):
        return packaging.version.parse(version)

    def get_parsed_system_version(self):
        return self.normalize_version_string(self.system.get_version())

    def get_version_major(self):
        return self.system.get_version().partition('.')[0]

    def _get_version_as_float(self):
        float_digit_list = self.system.get_version().split('.')[:2]
        return float(".".join(float_digit_list))

    def _init_fetatures(self):
        resp = self.system.api.get("_features", assert_success=False)
        if resp.response.status_code == httplib.NOT_FOUND:
            features_list = []  # Backwards compatible
        else:
            resp.assert_success()
            features_list = resp.get_result()
        self._features = dict((feature_info['name'], feature_info['version']) for feature_info in features_list)

    def _get_feature_version(self, feature_key, default_version=NOTHING):
        if self._features is None:
            self._init_fetatures()
        return self._features.get(feature_key, default_version)

    def _has_feature(self, feature_key):
        return self._get_feature_version(feature_key, NOTHING) is not NOTHING

    def set_feature_as_supported(self, feature_key, version=0):
        assert self._get_feature_version(feature_key, 0) <= version, "Cannot downgrade feature's supported version"
        self._features[feature_key] = version

    def has_npiv(self):
        return self._has_feature("fc/soft_targets")

    def has_replication(self):
        return int(self.get_version_major()) >= 2

    def get_nas_version(self):
        return self._get_feature_version('nas', 0)

    def has_nas(self):
        return self.get_nas_version() >= 2

    def has_network_configuration(self):
        return int(self.get_version_major()) >= 2

    def get_metadata_version(self):
        return self._get_feature_version('metadata', 1)

    def has_consistency_groups(self):
        return self._get_version_as_float() >= 2.2
