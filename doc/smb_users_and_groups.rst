SMB Users and Groups
====================


Creating a User
----------------

Create a user using the ``create`` method:

.. code-block:: python

        >>> user = system.smb_users.create()

Creating a Group
----------------

Create a group using the ``create`` method:

.. code-block:: python

        >>> group = system.smb_groups.create()


Adding a User to a Group
-------------------------

A user can be added to a group by using the ``update_groups`` method

.. code-block:: python

        >>> new_groups = user.get_groups() + [group]
        >>> user.update_groups(new_groups)
        >>> group in user.get_groups()
        True


Removing a User from a Group
------------------------------

A user can be added to a group by using the ``update_groups`` method

.. code-block:: python

        >>> new_groups = [g for g in user.get_groups() if g != group]
        >>> user.update_groups(new_groups)
        >>> group in user.get_groups()
        False

Setting a User's Primary Group
-------------------------------

A user's primary group can be set using the ``update_primary_group`` method:


.. code-block:: python

        >>> user.update_primary_group(group)
        >>> user.get_primary_group() == group
        True
