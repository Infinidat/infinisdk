S3 Buckets
==========

An **S3 bucket** is a container for storing objects. Each S3bucket belongs to one pool which in turn is associated with exactly one S3 account. The physical_capacity of the pool limits the combined capacity of all S3 buckets within the pool.

Creating Buckets
----------------

Buckets are created under a specific S3 account. Use ``system.s3_buckets.create`` and specify the account:

.. code-block:: python

   >>> account = system.s3_accounts.create(pool=pool, name="my_account")
   >>> bucket = system.s3_buckets.create(account=account, name="my-bucket")

Optional parameters include ``compression_enabled`` and ``ssd_enabled``:

.. code-block:: python

   >>> bucket = system.s3_buckets.create(
   ...     account=account,
   ...     name="logs",
   ...     compression_enabled=True,
   ...     ssd_enabled=False,
   ... )


Querying Buckets
----------------

List all buckets in the system:

.. code-block:: python

   >>> for bucket in system.s3_buckets.to_list():
   ...     print(bucket.get_name(), bucket.get_account().get_name())
   my-bucket my_account

Retrieve usage statistics:

.. code-block:: python

   >>> print(bucket.get_used_size())
   0 bit
   >>> print(bucket.get_object_count(), "objects")
   3 objects

Updating Buckets
----------------

Buckets can be updated with mutable fields such as ``compression_enabled`` and ``ssd_enabled``:

.. code-block:: python

   >>> bucket.enable_compression()
   >>> bucket.enable_ssd()

Deleting Buckets
----------------

Remove a bucket with:

.. code-block:: python

   >>> bucket.delete()