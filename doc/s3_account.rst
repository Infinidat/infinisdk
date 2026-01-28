S3 Accounts
===========

An **S3 account** represents a chargeable entity for S3 usage. Each S3 account must be associated with exactly one pool, and may contain multiple S3Users. Every S3Bucket and S3User is associated with exactly one S3Account.

Creating S3 Accounts
--------------------

Use ``system.s3_accounts.create`` to create an account. You must specify the target pool:

.. code-block:: python

   >>> pool = system.pools.create(type="S3", physical_capacity=TiB)
   >>> account = system.s3_accounts.create(pool=pool, name="my_account")

Additional optional parameters include ``email``, ``location``, and ``enabled``:

.. code-block:: python

   >>> account = system.s3_accounts.create(
   ...     pool=pool,
   ...     name="marketing",
   ...     email="team@example.com",
   ...     location="us-east-1",
   ...     enabled=True,
   ... )

Querying S3 Accounts
--------------------

List all accounts:

.. code-block:: python

   >>> for account in system.s3_accounts.to_list():
   ...     print(account.get_name(), account.get_pool().get_name())
   my_account my_pool

Retrieve usage statistics:

.. code-block:: python

   >>> print(account.get_capacity_consumed())
   320 KiB
   >>> print(account.get_buckets_count(), "buckets")
   1 buckets
   >>> print(account.get_users_count(), "users")
   1 users

Updating S3 Accounts
--------------------

Accounts can be updated with mutable fields such as ``name``, ``email``, ``location``, or ``enabled``:

.. code-block:: python

   >>> account.update_name("sales")
   >>> account.update_email("sales@example.com")
   >>> account.enable()

Deleting S3 Accounts
--------------------

Remove an account with:

.. code-block:: python

   >>> account.delete()