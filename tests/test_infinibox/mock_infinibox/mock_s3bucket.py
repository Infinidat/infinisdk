MOCK_S3_BUCKET_CREATE = {
    "result": {
        "id": 23,
        "tenant_id": 1,
        "account_id": 11111,
        "name": "Bucket-1",
        "created_at": 1605012653572,
        "updated_at": 1605012653572,
        "object_count": 3,
        "capacity_consumed": 0,
    },
    "error": None,
    "metadata": {"ready": True},
}

MOCK_S3_BUCKETS_GET = {
    "result": [
        {
        "id": 23,
        "tenant_id": 1,
        "account_id": 11111,
        "name": "my-bucket",
        "created_at": 1605012653572,
        "updated_at": 1605012653572,
        "object_count": 3,
        "capacity_consumed": 0,
        },
    ],
    "error": None,
    "metadata": {
    "ready": True,
    "number_of_objects": 1,
    "page_size": 50,
    "pages_total": 1,
    "page": 1
  }
}

MOCK_S3_BUCKET_GET = {
    "result": {
        "id": 23,
        "tenant_id": 1,
        "account_id": 11111,
        "name": "my-bucket",
        "created_at": 1605012653572,
        "updated_at": 1605012653572,
        "object_count": 3,
        "capacity_consumed": 0,
    },
    "error": None,
    "metadata": {"ready": True},
}