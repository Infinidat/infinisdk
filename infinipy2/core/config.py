import confetti


config = confetti.Config(dict(

    check_version_compatibility = True,

    defaults=dict(
        system_api_port=80,
    ),
    izbox=dict(
        defaults=dict(
            system_api=dict(
                timeout_seconds=180,
            ),
            events=dict(
                page_size=1000,
                max_events=10 ** 6,
                max_page_size=1000),
        ),
        approval_required_codes=tuple((
            "DANGEROUS_OPERATION",
        )),
    ),
    infinibox=dict(

        compatible_versions = [
            r"^1.5(?:[\.-].*)$",
            r"^1.6.0.0-dev",
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
