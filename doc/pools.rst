Pools
=====

Creating Pools
--------------

Creating pools is done with ``system.objects.pools.create``:

.. code-block:: python
		
		>>> p = system.pools.create()

You can also specify physical and virtual capacity:

.. code-block:: python

		>>> p = system.pools.create(physical_capacity=TiB, virtual_capacity=TiB)


Updating Pools
--------------

Updating fields such as name and capacities are done like any other object update operations in InfiniSDK:

.. code-block:: python
       
       >>> p.update_name('new_name')
       >>> p.update_physical_capacity(p.get_physical_capacity() * 2)

Deleting Pools
--------------

Deleting a pool is done using :meth:`.Pool.delete`:

.. code-block:: python
       
       >>> p.delete()
       >>> p.is_in_system()
       False


Administered Pools
------------------

Use :func:`infinisdk.infinibox.pool.PoolBinder.get_administered_pools` to obtain the list of pools the current user can administer:

.. code-block:: python

		>>> pools = system.pools.get_administered_pools()
