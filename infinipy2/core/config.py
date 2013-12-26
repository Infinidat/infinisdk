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
            ),
        ),
    infinibox=dict(
        defaults=dict(
            system_api=dict(
                username="infinidat",
                password="123456",
                timeout_seconds=30,
                ),
            ),
        ),
    ))
