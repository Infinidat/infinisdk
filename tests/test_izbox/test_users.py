
def test_has_users(izbox):
    assert izbox.users.find()

def test_create_user(izbox):
    user = izbox.users.create()
    assert user is not None
