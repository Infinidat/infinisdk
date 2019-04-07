.. _hooks:

Hooks
=====

Overview
--------
infinisdk uses `gossip` library, implementaion of a basic hook mechanism for registering callbacks.


.. code-block:: python

		>>> from __future__ import print_function
		>>> import gossip

		>>> @gossip.register('infinidat.sdk.post_object_creation', tags=['pool'], token=gossip_token)
		... def post_creation(obj, **_):
		...     print("Pool '{}' was created".format(obj.get_name()))

		>>> pool = system.pools.create(name='some_pool')
		Pool 'some_pool' was created

.. note:: It is entirely possible for hooks to receive more keyword arguments as features are added to InfiniSDK. To cope with this you are strongly encouraged to allow passing "catch-all" keyword arguments to your hooks (e.g. \*\*kwargs)

.. seealso:: For more information about gossip, see `Gossip documentation <https://gossip.readthedocs.io/en/latest/>`_


Available Hooks
---------------

The following hooks are available from the ``infinidat.sdk`` group:

.. hook_list_doc::

