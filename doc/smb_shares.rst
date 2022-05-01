SMB Shares
====================


Creating a Share
----------------

Create a share using the ``add_share`` method on the :class:`infinisdk.infinibox.filesystem.Filesystem` object:

.. code-block:: python

        >>> fs = system.filesystems.create(pool=pool, security_style="WINDOWS")
        >>> share = fs.add_share()
        >>> share in fs.get_shares()
        True


Share Permissions
-------------------------

Permissions can be accessed with the ``permissions`` field:

.. code-block:: python

        >>> perm = share.permissions.create(sid="S-1-1-1", access="NONE") # doctest: +SKIP
        >>> perm.update_access("FULLCONTROL") # doctest: +SKIP
        >>> perm.get_access() # doctest: +SKIP
        FULLCONTROL
        >>> share.permissions.get(sid="S-1-1-1") == perm # doctest: +SKIP
        True
        >>> perm in share.permissions.to_list() # doctest: +SKIP
        True
        >>> perm.delete() # doctest: +SKIP
        >>> perm in share.permissions.to_list() # doctest: +SKIP
        False

