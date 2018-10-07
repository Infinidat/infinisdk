User Management
===============

User management in InfiniSDK is done mostly via ``system.users`` and ``system.groups``.

Users
-----

Getting
~~~~~~~

Getting all users in a system

.. code-block:: python

	>>> users = system.users.to_list()

Getting a user by name

.. code-block:: python

	>>> user = system.users.get(name='someuser')
	>>> print(user.get_name())
	someuser


Creating and Deleting Users
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``infinibox.users.create`` to create new users:

.. code-block:: python

       >>> user = system.users.create(name='testuser', password='testpassword')

Deleting users is done like any other InfiniSDK object, using :meth:`.User.delete`:

.. code-block:: python

       >>> user.delete()

Modifying Users
~~~~~~~~~~~~~~~

You can modify users configured on the system using any of the :class:`.User` class:

.. code-block:: python

       >>> user = system.users.create(name='testuser', password='testpassword')
       >>> user.update_password('12345678')
       >>> user.update_name('testuser2')


Setting User Roles
~~~~~~~~~~~~~~~~~~

You can set a user's role using :meth:`.User.update_role`:

.. code-block:: python

       >>> user.update_role('PoolAdmin')
       >>> print(user.get_role())
       POOL_ADMIN

Setting Pool Owners
~~~~~~~~~~~~~~~~~~~

To set a pool that will be administered by a user, simply call :meth:`.Pool.set_owners`:

.. code-block:: python

       >>> pool = system.pools.create()
       >>> pool.set_owners([user])

LDAP Integration
----------------

Getting all current LDAP configs:


Setting up LDAP integration is done in two main steps. First, we need to define our LDAP settings:

.. code-block:: python

       >>> ldap_config = system.ldap_configs.define(name='AD2K3.local', domain_name='AD2K3.local', bind_username='Administrator', bind_password='passwd')

Once the LDAP directory is defined, we need to map the LDAP group to a local role:

.. code-block:: python

       >>> group = ldap_config.create_group(name='group01', dn='group01', role='PoolAdmin')
       >>> print(group.get_role())
       POOL_ADMIN


Updating LDAP Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Updating LDAP configurations can be easily done with :meth:`.LDAPConfig.modify`:

.. code-block:: python

       >>> ldap_config.modify(schema_group_class='group')

       >>> ldap_config.update_name('some_new_name')

Testing LDAP Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

       >>> ldap_config.test()

Updating LDAP Configuration Prioritiy Order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

       system.ldap_configs.set_order([ldap_config, ldap_config2, ...])


Reloading/Refreshing LDAP Cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

       >>> system.ldap_configs.reload()

Or:

.. code-block:: python

       >>> system.ldap_configs.flush_cache()




Deleting LDAP Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

       >>> ldap_config.delete()

