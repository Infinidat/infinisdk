import http.client as httplib
import operator
from ..core.config import config
from sentinels import NOTHING


class Feature:
    def __init__(self, name, version, enabled):
        self.name = name
        self.version = version
        self.enabled = enabled

def _get_predicate(opreator_func, value):
    def predicate(version):
        return opreator_func(version, value)
    return predicate

class Compatibility:

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
        return getattr(self, 'has_{}'.format(feature_name))()

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
        version_tuple = self.get_parsed_system_version().version[:2]
        return float(".".join(str(num) for num in version_tuple))

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

    def _has_feature(self, feature_key):
        return self._get_feature_version(feature_key, NOTHING) is not NOTHING

    def has_npiv(self):
        return self._has_feature('fc_soft_targets') or self._has_feature('fc/soft_targets')

    def has_replication(self):
        return int(self.get_version_major()) >= 2

    def has_iscsi(self):
        return self._has_feature('iscsi')

    def has_compression(self):
        return self._has_feature('compression')

    def has_nas(self):
        return self._get_feature_version('nas', 0) >= 2

    def has_network_configuration(self):
        return int(self.get_version_major()) >= 2

    def get_metadata_version(self):
        return self._get_feature_version('metadata', 1)

    def has_consistency_groups(self):
        return self.get_parsed_system_version() >= '2.2'

    def has_initiators(self):
        return self.get_parsed_system_version() >= '2.2'

    def has_user_disabling(self):
        return self._get_feature_version("user_management", 0) >= 1

    def has_auth_sessions(self):
        return self._has_feature('api_auth_sessions') or self._has_feature('api/auth_sessions')

    def has_max_speed(self):
        return self.get_parsed_system_version() > '2.2'

    def has_writable_snapshots(self):
        return self._has_feature('snapshots')

    def has_sync_job_states(self):
        return self.get_parsed_system_version() >= '3.0'

    def has_sync_replication(self):
        return self.get_parsed_system_version() >= '4.0'

    def has_nas_replication(self):
        return self._has_feature('filesystem_replicas')

    def has_qos(self):
        return self._has_feature('qos')

    def has_treeq(self):
        return self._has_feature('treeq')

    def has_openvms(self):
        return self._has_feature('open_vms')

    def has_dot_snapshot(self):
        return self._has_feature('dot_snapshots')

    def has_tenants(self):
        return self._has_feature('tenants')

    def has_snapshot_lock(self):
        return self.get_parsed_system_version() >= '4.0.30'

    def has_auto_respawn(self):
        return self.get_parsed_system_version() >= '4.0.30'

    def has_active_active(self):
        return self._has_feature('active_active')

    def has_active_active_preferred_on_replica(self):
        return self._get_feature_version("active_active", 0) > 0

    def has_nlm(self):
        return self._has_feature('nlm')

    def has_local_users_auth(self):
        return self._has_feature('local_users_auth')

    def has_fips(self):
        return self._has_feature('fips')

    def has_replica_auto_create(self):
        return self._has_feature('replica_auto_create')

    def has_active_active_cg(self):
        return self._get_feature_version("active_active", 0) > 1

    def has_events_db(self):
        return self._has_feature('events_db')

    def has_concurrent_replication(self):
        return self._get_feature_version("active_active", 0) > 2

    def has_kms(self):
        return  self._has_feature('kms')

    def has_event_retention(self):
        return self._has_feature('event_retention')


_VERSION_TUPLE_LEN = 5


class _InfiniboxVersion:

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
        if self._is_odd_version:
            extra_info += " (unknown structure)"
        return "<InfiniboxVersion: {}{}>".format(self.version, extra_info)
