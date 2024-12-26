NFS Server Capabilities
=======================

These are NFS settings at the level of the tenant, so there is one configuration per tenant.

Getting Current Server Capabilities
-----------------------------------
You can get the current configuration by:

.. code-block:: python

   >>> system.get_nfs_server_capabilities()
   Munch({'tenant_id': 1, 'nfsv4_support': 'DISABLED'})

The default tenant NFS server capabilities will be returned. You should expect the following fields to be returned:

* `nfsv4_support`

Updating Server Capabilities
----------------------------

To update a field, e.g., `nfsv4_support`:

.. code-block:: python

   >>> system.update_nfs_server_capabilities(nfsv4_support="enabled") 

`nfsv4_support` indicates what is the NFSv4 support required when creating an export, the values can be:

* `Enabled` - both NFSv4 and NFSv3 are possible.
* `Disabled` - (the default), only NFSv3 is possible.
* `Required` - only NFSv4 is possible.
