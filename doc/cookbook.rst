Cookbook
========

Below are several common tasks and how to accomplish them using InfiniSDK.


Authentication
--------------

Saving credentials for reuse without login
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some cases it is useful to save the authentication information for later, in order to avoid an unnecessary login event. It can be used, for instance,
for scripts that are being constantly rerun at high frequency.

To do that, use :meth:`.API.save_credentials` and :meth:`.API.load_credentials`:

.. code-block:: python
       
       >>> import pickle
       >>> import tempfile
       >>> import os

       >>> filename = os.path.join(tempfile.mkdtemp(), 'creds')

       >>> creds = system.api.save_credentials()
       >>> with open(filename, 'wb') as f:
       ...     pickle.dump(creds, f)
       
.. code-block:: python
       
       >>> import pickle
       >>> with open(filename, 'rb') as f:
       ...     creds = pickle.load(f)
       >>> creds = system.api.load_credentials(creds)
       



Objects
-------

Determining if an object is of a certain type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
       
       >>> assert isinstance(pool, system.pools.object_type)
       >>> assert not isinstance(pool, system.volumes.object_type)

