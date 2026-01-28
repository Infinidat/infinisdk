S3 Users
========

An **S3 user** represents an identity within an S3 account. Each S3User belongs to exactly one S3 account, and may contain multiple S3Credentials.


Creating Users
--------------

Users are created under a specific S3 account. Use ``system.s3_users.create`` and specify the account:

.. code-block:: python

   >>> account = system.s3_accounts.create(pool=pool, name="my_account")
   >>> user = system.s3_users.create(account=account, name="alice")

Optional parameters include ``root``, ``description``, ``uid``, ``gid``, and ``status``:

.. code-block:: python

   >>> user = system.s3_users.create(
   ...     account=account,
   ...     name="bob",
   ...     root=True,
   ...     description="Admin user for account",
   ...     uid=1001,
   ...     gid=1001,
   ... )

Creating Multiple Users
-----------------------

Use ``create_many`` to generate multiple users with a single call:

.. code-block:: python

   >>> users = system.s3_users.create_many(account=account, count=2, name="team")

Querying Users
--------------

List all users in the system:

.. code-block:: python

   >>> for user in system.s3_users.to_list():
   ...     print(user.get_name(), user.get_account().get_name())
   team-2 my_account
   team-1 my_account

Retrieve user metadata:

.. code-block:: python

   >>> print(user.get_status())
   ENABLED
   >>> print(user.get_last_used())
   2025-08-17T07:21:16.048000+00:00

Updating Users
--------------

Several fields are mutable, including ``status``, ``description``, ``uid``, ``gid``, and ``root``:

.. code-block:: python

   >>> user.update_status("DISABLED")
   >>> user.update_description("Read-only user")
   >>> user.update_gid(2000)

Deleting Users
--------------

Remove a user with:

.. code-block:: python

   >>> user.delete()