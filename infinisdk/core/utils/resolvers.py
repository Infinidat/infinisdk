from ..exceptions import ObjectNotFound


def schedules_resolver(system, api_value):
    """
    Returns a schedule with id=api_value.
    This is for cases when you can't get
    to the schedule from its parent policy,
    e.g. when dealing with SG and its snapshots
    which don't get the policy copied from the
    MASTER entity.
    """
    for policy in system.snapshot_policies.to_list():
        try:
            return policy.schedules.get_by_id(api_value)
        except ObjectNotFound:
            continue
    raise ObjectNotFound(f"Schedule with id={api_value} was not found")
