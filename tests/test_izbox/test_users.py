
def test_has_users(system):
    assert system.users.find()

def test_create_user(system):
    user = system.users.create()
    assert user is not None
