import operator

from sentinels import NOTHING
from vintage import deprecated

from .._compat import httplib
from ..core.config import config


class Feature(object):
    def __init__(self, name, version, enabled):
        self.name = name
        self.version = version
        self.enabled = enabled

def _get_predicate(opreator_func, value):
    def predicate(version):
        return opreator_func(version, value)
    return predicate

class Compatibility(object):

    def __init__(self, system):
        self.system = system
        self._features = None
        self._system_version = None

    def invalidate_cache(self):
        self._features = None
        self._system_version = None

    def is_initialized(self):
        return self._features is not None

    def initialize(self):
        if not self.is_initialized():
            self._init_features()

    def can_run_on_system(self):
        version_string = self.system.get_version().split('-', 1)[0]
        system_version = self.normalize_version_string(version_string)
        restrictions = self._parse_restrictions(config.root.infinibox.compatible_versions)
        return all(restriction(system_version) for restriction in restrictions)

    def _parse_restrictions(self, restrictions):
        returned = []
        for restriction in restrictions:
            operator_name, value = restriction.split(':', 1)
            op = getattr(operator, operator_name)
            returned.append(_get_predicate(op, value))
        return returned

    def is_feature_supported(self, feature_name):
        if feature_name is NOTHING:
            return True
        return getattr(self, 'has_{0}'.format(feature_name))()

    def normalize_version_string(self, version):
        return _InfiniboxVersion.parse(version)

    def get_parsed_system_version(self):
        if self._system_version is None:
            self._system_version = self.normalize_version_string(
                self.system.get_version())
        return self._system_version

    def get_version_major(self):
        return self.system.get_version().partition('.')[0]

    def get_version_as_float(self):
        float_digit_list = self.system.get_version().split('.')[:2]
        return float(".".join(float_digit_list))

    def _init_features(self):
        resp = self.system.api.get("_features", assert_success=False)
        if resp.response.status_code == httplib.NOT_FOUND:
            features_list = []  # Backwards compatible
        else:
            resp.assert_success()
            features_list = resp.get_result()
        self._features = dict((feature_info['name'], Feature(feature_info['name'], feature_info['version'],
                                                             feature_info.get('enabled', True)))
                              for feature_info in features_list)

    def _get_feature_version(self, feature_key, default_version=NOTHING):
        if self._features is None:
            self._init_features()
        feature = self._features.get(feature_key, None)
        if feature is None or not feature.enabled:
            return default_version
        return feature.version

    def has_feature(self, feature_key):
        return self._get_feature_version(feature_key, NOTHING) is not NOTHING

    def has_npiv(self):
        return self.has_feature('fc_soft_targets') or self.has_feature('fc/soft_targets')

    def has_replication(self):
        return int(self.get_version_major()) >= 2

    def has_iscsi(self):
        return self.has_feature('iscsi')

    def has_compression(self):
        return self.has_feature('compression')

    def has_nas(self):
        return self._get_feature_version('nas', 0) >= 2

    def has_network_configuration(self):
        return int(self.get_version_major()) >= 2

    def get_metadata_version(self):
        return self._get_feature_version('metadata', 1)

    def has_consistency_groups(self):
        return self.get_version_as_float() >= 2.2

    def has_initiators(self):
        return self.get_version_as_float() >= 2.2

    def has_user_disabling(self):
        return self._get_feature_version("user_management", 0) >= 1

    def has_auth_sessions(self):
        return self.has_feature('api_auth_sessions') or self.has_feature('api/auth_sessions')

    def has_max_speed(self):
        return self.get_version_as_float() > 2.2

    def has_writable_snapshots(self):
        return self.has_feature('snapshots')

    @deprecated('Use has_writable_snapshots instead', since='65.0')
    def has_snapclones(self):
        self.has_writable_snapshots()

    def has_sync_job_states(self):
        return self.get_version_as_float() >= 3.0

    def has_sync_replication(self):
        return self.get_version_as_float() >= 4.0

    def has_nas_replication(self):
        return self.has_feature('filesystem_replicas')

    def has_qos(self):
        return self.has_feature('qos')

_VERSION_TUPLE_LEN = 5


class _InfiniboxVersion(object):

    def __init__(self, version_tuple, is_dev, is_odd=False):
        self.version = version_tuple
        self._is_dev = is_dev
        self._is_odd_version = is_odd

    @classmethod
    def parse(cls, version):
        if isinstance(version, _InfiniboxVersion):
            return version
        before_dash, _, after_dash = version.partition('-')
        is_dev = is_odd = False
        parsed_version = tuple(int(ver_digit)
                               for ver_digit in before_dash.split('.'))

        if after_dash:
            if after_dash.startswith('dev'):
                is_dev = True
            elif len(after_dash) > 1:
                is_odd = True
            else:
                parsed_version += (after_dash, )

        parsed_version += tuple(('*' if index >= 4 else 0) for index in range(
            len(parsed_version), _VERSION_TUPLE_LEN))
        return cls(parsed_version, is_dev, is_odd=is_odd)

    def __eq__(self, other):
        other_ver = self.parse(other)
        if self.version != other_ver.version:
            return False
        if self._is_odd_version or other_ver._is_odd_version:  # pylint: disable=protected-access
            return False

        if self._is_dev or other_ver._is_dev:  # pylint: disable=protected-access
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        # pylint: disable=protected-access
        other_ver = self.parse(other)
        if self.version == other_ver.version:
            if self._is_odd_version or other_ver._is_odd_version or (self._is_dev and other_ver._is_dev):
                return str(self) < str(other)
            if self._is_dev ^ other_ver._is_dev:
                return self._is_dev
            return False  # we're identical -- both not odd, and no dev on either side

        return self.version < other_ver.version  # we judge by the version tuple

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return not self == other and not self < other

    def __ge__(self, other):
        return self == other or self > other

    def __repr__(self):
        extra_info = ""
        if self._is_dev:
            extra_info += " dev version"
        if not self._is_odd_version:
            extra_info += " (unknown structure)"
        return "<InfiniboxVersion: {0}{1}>".format(self.version, extra_info)
