Replication
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

To allow for snapshot replication you would use something like the following:

.. code-block:: python

   from datetime import timedelta

   replica = primary_system.replicas.replicate_entity(vol, link=link, remote_pool=remote_pool,
       including_snapshots=True, snapshots_retention=3600,
       lock_remote_snapshot_retention=timedelta(seconds=3600),
       rpo=timedelta(seconds=4), sync_interval=timedelta(seconds=4))

`lock_remote_snapshot_retention` is an optional parameter. It places a lock on the exposed snapshot
for a duration defined by the parameter's value (number of seconds since the original snapshot was created).
For an explanation about `rpo` and `sync_interval` parameters please see section below on RgReplica.

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

VVOL Replication
----------------
InfiniBox release 7.1 and above supports replication of VMware Virtual Volumes (vVols). 
Using vVols replication, VM administrators can easily set up efficient array-based replication for their virtual machines (VMs) directly from the same VMware vCenter user interface from which they control all other aspects of their VMs.

Setting up vVols replication with InfiniBox consists of an initial setup, performed by the storage administrator, and an ongoing setup, performed by the VM administrator.

As part of the initial setup, the storage administrator defines vVols Replication Groups and replicas.
For this process to succeed the user is expected to provide a *link* (an instance of :class:`infinisdk.infinibox.link.Link`, representing the network link to the remote system). You can get the remote system from the link object by:

.. code-block:: python

        >>> link.get_linked_system()  # doctest: +SKIP

Initial Setup for VVOL Replication
----------------------------------
A storage administrator may create one or more vVols Replication Groups. A separate replica is created for each group.

* A vVols Replication Group contains multiple vVols, typically from a set of virtual machines
* The replica defines the target InfiniBox system where the replicated vVols will be available.

Creating Replication Group
--------------------------
To create a Replication Group (RG) you'll also need to create a *pool* (an instance of :class:`infinisdk.infinibox.pool.Pool`) with `type="VVOL"`:

.. code-block:: python

        >>> vvol_pool = system.pools.create(name="pool1", type="VVOL")  # doctest: +SKIP
        >>> rg = system.replication_groups.create(pool=vvol_pool)  # doctest: +SKIP

Creating a Replica (RgReplica)
------------------------------
In addition to the above you'll also need to create a remote pool with `type="VVOL"` for the remote system in the same way:

.. code-block:: python

        >>> remote_system = link.get_linked_system()  # doctest: +SKIP
        >>> remote_vvol_pool = remote_system.pools.create(name="pool1-remote", type="VVOL")  # doctest: +SKIP
        >>> from datetime import timedelta  # doctest: +SKIP
        >>> rg_replica = system.rg_replicas.create(link=link, sync_interval=timedelta(seconds=60),rpo=timedelta(seconds=120), remote_pool_id=remote_vvol_pool.get_id(), replication_group=rg)  # doctest: +SKIP

.. note:: The `sync_interval` parameter controls how often the system will replicate the data (e.g. every 60 seconds)

.. note:: The `rpo` value is the Recovery Point Objective value and it represents the tolerance to data loss during the replication process. It should be greater than the `sync_interval` value. E.g. if this value is 120 seconds and `sync_interval` is 60 seconds then the system will replicate every 60 seconds and will raise an alert if there was an issue and the system missed 2 replication attempts (2 intervals).
