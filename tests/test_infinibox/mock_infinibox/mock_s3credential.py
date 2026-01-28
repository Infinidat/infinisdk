MOCK_CREDENTIAL_CREATE = {
    "result": {
        "id": 41,
        "access_key": "AKIAEXAMPLE",
        "status": "ENABLED",
        "description": "Example",
        "last_used": 1740031467773,
        "created_at": 1740031467773,
        "updated_at": 1740031467773,
        "tenant_id": 1,
        "user_id": 41,
    },
    "error": None,
    "metadata": {"ready": True},
}

MOCK_CREDENTIAL_MODIFY = {
    "result": {
        "id": 41,
        "access_key": "AKIAEXAMPLE",
        "status": "DISABLED",
        "description": "Example2",
        "last_used": 1740031467773,
        "created_at": 1740031467773,
        "updated_at": 1740031467773,
        "tenant_id": 1,
        "user_id": 41,
    },
    "error": None,
    "metadata": {"ready": True},
}


MOCK_CREDENTIALS_GET = {
  "result": [
    {
        "id": 41,
        "access_key": "AKIAEXAMPLE1",
        "status": "DISABLED",
        "description": "Example2",
        "last_used": 1740031467773,
        "created_at": 1740031467773,
        "updated_at": 1740031467773,
        "tenant_id": 1,
        "user_id": 41,
    },
    {
        "id": 42,
        "access_key": "AKIAEXAMPLE2",
        "status": "ENABLED",
        "description": "Example",
        "last_used": 1740031467773,
        "created_at": 1740031467773,
        "updated_at": 1740031467773,
        "tenant_id": 1,
        "user_id": 41,
    },
  ],
  "error": None,
  "metadata": {
    "ready": True,
    "number_of_objects": 2,
    "page_size": 50,
    "pages_total": 1,
    "page": 1
  }
}