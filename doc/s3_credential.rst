S3 Credentials
==============

An **S3 credential** is a combination of access_key and secret_key, along with an optional description. Each access_key is unique for the entire system. Each S3Credential always belongs to exactly one S3User.
Creating Credentials

--------------------

To create a credential, pass the user it belongs to:

.. code-block:: python

   >>> user = system.s3_users.create(account=account, name="app-user")
   >>> credential = system.s3_credentials.create(user=user)

By default, an ``access_key`` and ``secret_key`` will be generated automatically if not provided.  
You may optionally pass explicit values:

.. code-block:: python

   >>> credential = system.s3_credentials.create(
   ...     user=user,
   ...     access_key="AKIAEXAMPLE",
   ...     secret_key="secret123",
   ...     description="Credential for CI/CD pipeline",
   ... )

Creating Multiple Credentials
-----------------------------

Use ``create_many`` to generate multiple credentials with one call:

.. code-block:: python

   >>> creds = system.s3_credentials.create_many(user=user, count=2)
   >>> [c.get_access_key() for c in creds]
   ['AKIAEXAMPLE', 'AKIAEXAMPLE']

Querying Credentials
--------------------

List all credentials in the system:

.. code-block:: python

   >>> for cred in system.s3_credentials.to_list():
   ...     print(cred.get_user().get_name(), cred.get_access_key())
   team-1 AKIAEXAMPLE1
   team-1 AKIAEXAMPLE2

Check metadata:

.. code-block:: python

   >>> print(credential.get_status())
   ENABLED
   >>> print(credential.get_last_used())
   2025-02-20T06:04:27.773000+00:00

Updating Credentials
--------------------

Mutable fields include ``status`` and ``description``:

.. code-block:: python

   >>> credential.update_status("DISABLED")
   >>> credential.update_description("Disabled after key rotation")

Deleting Credentials
--------------------

Remove a credential with:

.. code-block:: python

   >>> credential.delete()