SMB Server Capabilities
=======================

These are SMB settings at the level of the tenant, so there is one configuration per tenant.

Getting Current Server Capabilities
-----------------------------------
You can get the current configuration by:

.. code-block:: python

   >>> system.get_smb_server_capabilities() # doctest: +SKIP

The default tenant SMB server capabilities will be returned. You should expect the following fields to be returned:

* `min_smb_protocol`
* `max_smb_protocol`
* `smb_signing`
* `smb_encryption`

Updating Server Capabilities
----------------------------

To update a field, e.g. `encryption`:

.. code-block:: python

   >>> system.update_smb_server_capabilities(smb_encryption="disabled")  # doctest: +SKIP
