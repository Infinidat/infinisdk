MOCK_USER_CREATION = {
    "result": {
        "id": 2,
        "name": "user1",
        "role": "ADMIN",
        "email": "user1@email.com",
    }
}

MOCK_USER_CHANGE_PASSWORD = {
    "result": {
        "id": -2,
        "success": True,
        "message": "Password changed successfully"
    },
    "error": None,
    "metadata": {
        "ready": True
    }
}


MOCK_USER_CREATION_FOR_CHANGE_PASSWORD = {
    "result": {
        "id": 2,
        "name": "admin",
        "role": "ADMIN",
        "email": "dev.mgmt@infinidat.com",
    }
}