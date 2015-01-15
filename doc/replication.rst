External Replication
====================


Creating Replicas
-----------------

Replicating a volume to a remote system (mirroring) can be done by calling the *replicate_volume* shortcut:

.. code-block:: python
       
       >>> pool = primary.pools.create()
       >>> vol = primary.volumes.create(pool=pool)
       >>> remote_pool = secondary.pools.create()
       >>> replica = primary.replicas.replicate_volume(vol, link=link, remote_pool=remote_pool)

.. note:: the above example assumes you already have a :class:`infinisdk.infinibox.link.Link` object.

.. seealso:: :class:`infinisdk.infinibox.replica.Replica`
