from urlobject import URLObject
from ..conftest import relevant_from_version


# Soft targets supported (on simulator) >= 3.0 (altough in real system its supported >= 1.7)
@relevant_from_version('3.0')
def test_fc_soft_target_url_path(infinibox):
    assert isinstance(infinibox.fc_soft_targets.get_url_path(), URLObject)


# Soft targets supported (on simulator) >= 3.0 (altough in real system its supported >= 1.7)
@relevant_from_version('3.0')
def test_fc_soft_target_query(infinibox):
    COUNT = 3
    assert infinibox.fc_soft_targets.count() == 0
    fc_switch = infinibox.fc_switches.choose()
    soft_targets = infinibox.fc_soft_targets.create_many(quantity=COUNT, switch=fc_switch)
    assert isinstance(soft_targets, list)
    assert all(isinstance(target, infinibox.fc_soft_targets.object_type) for target in soft_targets)
