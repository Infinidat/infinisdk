External Replication
====================


Creating Async Replicas
-----------------------

Replicating a volume to a remote system (mirroring) can be done by calling the *replicate_volume* shortcut:

.. code-block:: python
       
       >>> pool = primary.pools.create()
       >>> vol = primary.volumes.create(pool=pool)
       >>> remote_pool = secondary.pools.create()
       >>> replica = primary.replicas.replicate_volume(vol, link=link, remote_pool=remote_pool)

.. note:: the above example assumes you already have a :class:`infinisdk.infinibox.link.Link` object.

.. seealso:: :class:`infinisdk.infinibox.replica.Replica`


Replicating Consistency Groups
------------------------------

Creating a CG replica is also straightforward, and is done via the ``replicate_cons_group`` method:

.. code-block:: python
       
       >>> cg = primary.cons_groups.create(pool=pool)       
       >>> replica = primary.replicas.replicate_cons_group(cg, link=link, remote_pool=remote_pool)

Creating Synchronous Replicas
-----------------------------

Creating synchronous replicas is done by specifying ``"SYNC"`` for the ``replication_type`` parameter during replica creation:


.. code-block:: python
       
       >>> replica = primary_system.replicas.replicate_entity(
       ...     volume1, link=link, 
       ...     replication_type="SYNC", remote_pool=remote_pool)


.. note:: The default for the ``replication_type`` argument is ``"ASYNC"``.
