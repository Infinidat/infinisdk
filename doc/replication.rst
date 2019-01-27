External Replication
====================


Creating Async Replicas
-----------------------

Replicating a volume or a filesystem to a remote system (mirroring) can be done by calling the *replicate_entity* shortcut:

.. code-block:: python

       >>> pool = primary_system.pools.create()
       >>> vol = primary_system.volumes.create(pool=pool)
       >>> remote_pool = secondary_system.pools.create()
       >>> replica = primary_system.replicas.replicate_entity(vol, link=link, remote_pool=remote_pool)


The default behavior for :meth:`.ReplicaBinder.replicate_entity` is to create the remote entity (receiving a remote pool as input).
You can also use an existing remote entity through the :meth:`.ReplicaBinder.replicate_entity_use_base` shortcut:

.. code-block:: python

       replica = primary_system.replicas.replicate_entity_use_base(
           local_entity,
           link=link,
           local_snapshot=snap,
           remote_snapshot=remote_snap)

Replication creation requires the following arguments to be provided:

* A *local entity* (e.g. volume, filesystem or consistency group)
* A *link* (an instance of :class:`infinisdk.infinibox.link.Link`, representing the network link to the remote system)

As for the remote entity, it depends on the scenario being used to create the replica:

* Using a base snapshot (`_use_base`) requires a remote and local snapshots
* Creating a new entity on the remote side (`_create_target` or default) requires the remote pool to be provided
* Creating over an existing, formatted target (`_existing_target`) requires the remote target to be provided via ``remote_entity`` parameter



.. seealso:: :class:`infinisdk.infinibox.replica.Replica`

.. note:: The type of the replica created (async/sync) is controlled by an optional parameter called ``replication_type``. The default, if not specified, is ``"ASYNC"``.



Replicating Consistency Groups
------------------------------

Creating a CG replica is also straightforward, and is done via the ``replicate_cons_group`` method:

.. code-block:: python

       >>> cg = primary_system.cons_groups.create(pool=pool)
       >>> replica = primary_system.replicas.replicate_cons_group(cg, link=link, remote_pool=remote_pool)


Creating Synchronous Replicas
-----------------------------

Creating synchronous replicas is done by specifying ``"SYNC"`` for the ``replication_type`` parameter during replica creation:


.. code-block:: python

       >>> pool = primary_system.pools.create()
       >>> vol = primary_system.volumes.create(pool=pool)
       >>> replica = primary_system.replicas.replicate_entity(
       ...     vol, link=link,
       ...     replication_type="SYNC", remote_pool=remote_pool)


Changing Replication Type
-----------------------------

Changing the type of the replication to ``SYNC`` / ``ASYNC`` can be done by calling to ``change_type_to_sync`` / ``change_type_to_async`` respectively.
The replica must not be in ``INITIALIZING`` state. For example:


.. code-block:: python

        >>> async_replica.change_type_to_sync()
        >>> assert async_replica.is_type_sync()
        >>> async_replica.change_type_to_async()
        >>> assert async_replica.is_type_async()
