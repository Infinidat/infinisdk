import confetti
import os
from configparser import ConfigParser


config = confetti.Config(dict(

    check_version_compatibility=True,

    ini_file_path="~/.infinidat/infinisdk.ini",

    api={
        'log': {
            'pretty_json': False,
        }
    },

    defaults=dict(
        system_api_port=80,
        retry_sleep_seconds=5,
    ),
    infinibox=dict(

        compatible_versions=[
            "ge:2.0",
        ],

        defaults=dict(
            system_api=dict(
                timeout_seconds=30,
            ),
            enlosure_drives=dict(
                total_count=dict(mock=0, simulator=480),
            ),
        ),
        approval_required_codes=tuple((
            "APPROVAL_REQUIRED",
            "APPROVAL_REQUIRED_VOLUME_HAS_CHILDREN",
        )),
    ),

))

_cached_ini_parser = None

def get_ini_option(section, option, default=None):
    global _cached_ini_parser  # pylint: disable=global-statement
    if _cached_ini_parser is None:
        _cached_ini_parser = ConfigParser()
        _cached_ini_parser.read(os.path.expanduser((config.root.ini_file_path)))

    if _cached_ini_parser.has_option(section, option):
        return _cached_ini_parser.get(section, option)
    return default
