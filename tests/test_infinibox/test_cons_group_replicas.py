from ..conftest import relevant_from_version


@relevant_from_version('3.0')
def test_member_get_remote_entities(cg_replica):
    local_members = cg_replica.get_local_entity().get_members().to_list()
    remote_members = cg_replica.get_remote_entity().get_members().to_list()
    assert all(local_members)
    assert local_members
    assert all(remote_members)
    assert remote_members
    for local_member, remote_member in zip(local_members, remote_members):
        assert local_member.get_remote_entities() == [remote_member]
        assert local_member.get_remote_entity() == remote_member
        assert remote_member.get_remote_entities() == [local_member]
        assert remote_member.get_remote_entity() == local_member
