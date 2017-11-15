External Replication
====================


Creating Async Replicas
-----------------------

Replicating a volume or a filesystem to a remote system (mirroring) can be done by calling the *replicate_entity* shortcut:

.. code-block:: python
       
       >>> pool = primary.pools.create()
       >>> vol = primary.volumes.create(pool=pool)
       >>> remote_pool = secondary.pools.create()
       >>> replica = primary.replicas.replicate_entity(vol, link=link, remote_pool=remote_pool)

.. note:: the above example assumes you already have a :class:`infinisdk.infinibox.link.Link` object.

The default behavior for :meth:`.ReplicaBinder.replicate_entity` is to create the remote entity (receiving a remote pool as input).
You can also use an existing remote entity through the :meth:`.ReplicaBinder.replicate_entity_use_base` shortcut:

.. code-block:: python
       
       >>> replica = primary.replicas.replicate_entity_use_base(
       ...     local_entity,
       ...     link=link,
       ...     local_snapshot=snap,
       ...     remote_snapshot=remote_snap)


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
