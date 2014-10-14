Pools
=====

Creating Pools
--------------

Creating pools is done with ``system.objects.pools.create``:

.. code-block:: python
		
		>>> p = system.objects.pools.create()

You can also specify physical and virtual capacity:

.. code-block:: python

		>>> p = system.objects.pools.create(physical_capacity=TiB, virtual_capacity=TiB)


Administered Pools
------------------

Use :func:`infinisdk.infinibox.pool.PoolBinder.get_administered_pools` to obtain the list of pools the current user can administer:

.. code-block:: python

		>>> pools = system.objects.pools.get_administered_pools()
