from datetime import timedelta, time

def test_assign_entity(infinibox, filesystem, volume, volume1, cg):
    policy1 = infinibox.snapshot_policies.create()
    policy1.assign_entity(entity=filesystem)
    all_assigned_entities = policy1.get_assigned_entities()
    assert all_assigned_entities[0].assigned_entity_type is not None and \
           all_assigned_entities[0].assigned_entity_id is not None and \
           all_assigned_entities[0].assigned_entity_name is not None and \
           all_assigned_entities[0].snapshot_policy_id is not None and \
           all_assigned_entities[0].snapshot_policy_name is not None
    assert len(all_assigned_entities) == policy1.get_assigned_entities_count(from_cache=False) == 1
    assert any(filesystem.id == entity.assigned_entity_id for entity in all_assigned_entities)
    policy1.unassign_entity(filesystem)
    assert policy1.get_assigned_entities_count(from_cache=False) == 0
    assert len(policy1.get_assigned_entities()) == 0
    cg.add_member(volume)
    policy1.assign_entity(entity=cg)
    all_assigned_entities = policy1.get_assigned_entities()
    assert len(all_assigned_entities) == policy1.get_assigned_entities_count(from_cache=False) == 1
    assert any(cg.id == entity.assigned_entity_id for entity in all_assigned_entities)
    policy1.unassign_entity(cg)
    assert policy1.get_assigned_entities_count(from_cache=False) == 0
    assert len(policy1.get_assigned_entities()) == 0
    # using volume1 because it is not part of the cg
    # snapshot policies cannot be assigned to cg members
    policy1.assign_entity(entity=volume1)
    all_assigned_entities = policy1.get_assigned_entities()
    assert len(all_assigned_entities) == policy1.get_assigned_entities_count(from_cache=False) == 1
    assert any(volume1.id == entity.assigned_entity_id for entity in all_assigned_entities)

def test_schedule(infinibox):
    policy1 = infinibox.snapshot_policies.create()
    schedule_periodic = policy1.schedules.create(name="test1", interval=timedelta(seconds=7200), retention=timedelta(seconds=3600))
    schedule_clock = policy1.schedules.create(name="test2", type="clock", day_of_week="sunday",time_of_day=time(20,30,10), retention=timedelta(seconds=3600))
    assert schedule_periodic.get_fields()
    assert schedule_periodic.get_snapshot_policy() == policy1
    assert schedule_periodic.get_retention() == timedelta(seconds=3600)
    assert schedule_periodic.get_time_of_day() is None
    assert schedule_clock.get_fields()
    assert schedule_clock.get_time_of_day is not None
    assert schedule_clock.get_day_of_week().lower() == "sunday"

def test_create_two_policies_different_suffix(infinibox):
    policy1 = infinibox.snapshot_policies.create()
    policy2 = infinibox.snapshot_policies.create()
    assert policy1.get_suffix() != policy2.get_suffix()

def test_default_snapshot_policy(infinibox, volume, volume1, pool):
    assert volume.get_snapshot_policy() == volume1.get_snapshot_policy()
    assert volume.get_snapshot_policy().is_default_snapshot_policy()
    policy1 = infinibox.snapshot_policies.create()
    vol1 = infinibox.volumes.create(snapshot_policy=policy1, pool=pool)
    assert vol1.get_snapshot_policy() == policy1
    assert not vol1.get_snapshot_policy().is_default_snapshot_policy()
    policy1.assign_entity(entity=volume)
    assert not volume.get_snapshot_policy(from_cache=False).is_default_snapshot_policy()

def test_created_by_schedule_fields(volume_snapshot_and_schedule, volume):
    volume_snapshot, schedule = volume_snapshot_and_schedule
    assert volume_snapshot.get_created_by_schedule_name() == schedule.get_name()
    assert volume_snapshot.get_created_by_schedule() == schedule
    assert not volume.get_created_by_schedule()
    assert not volume.get_created_by_schedule_name()

def test_pagination_for_assigned_entities(infinibox, pool):
    policy1 = infinibox.snapshot_policies.create()
    infinibox.volumes.create_many(count=5, pool=pool)
    vol_list = infinibox.volumes.to_list()
    for vol in vol_list:
        policy1.assign_entity(entity=vol)

    assert len(policy1.get_assigned_entities()) == 5
    assert len(policy1.get_assigned_entities(page_size=1, page=1)) == 1
    assert len(policy1.get_assigned_entities(page_size=2, page=1)) == 2
    assert len(policy1.get_assigned_entities(page_size=2, page=2)) == 2
    unique_volumes_ids = set()
    for i in range(1, 6):
        unique_volumes_ids.add(policy1.get_assigned_entities(page_size=1, page=i)[0].assigned_entity_id)
    assert len(unique_volumes_ids) == 5
