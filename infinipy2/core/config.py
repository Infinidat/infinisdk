import confetti


config = confetti.Config(dict(
    defaults = dict(
        system_api_port=80,
        ),
    izbox=dict(
        defaults=dict(
            system_api=dict(
                username="infinidat",
                password="123456",
                timeout_seconds=180,
                ),
            events = dict(
                page_size=1000,
                max_events=10**6,
                max_page_size=1000),
            ),
        ),
    infinibox=dict(
        defaults=dict(
            system_api=dict(
                username="infinidat",
                password="123456",
                timeout_seconds=30,
                ),
            enlosure_drives=dict(
                total_count=dict(mock=0, simulator=480),
                ),
            ),
        ),
    ))
