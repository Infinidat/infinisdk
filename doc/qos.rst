Quality of Service
==================

Introduction
------------

Quality of Service policies allow to flexibly define the performance level for a given entity (e.g. a pool or a dataset).

Performance upper limit can be set in IOPS or in bandwidth (Mbps, Gbps, etc). Also, a burst can be defined, to allow the limits be exceeded for short periods.

Creation
--------
The ``QosPolicy`` is an object, which has the same fields as the corresponding InfiniBox object.
Creating a policy is done by using the :func:`create <infinisdk.infinibox.qos_policy.QosPolicy.create>` method:

.. code-block:: python

	>>> qos_policy = system.qos_policies.create(type='volume', max_ops=1000, name='my_policy')

The 'type' field must be one of: 'volume', 'pool_volume'.

Manipulation
------------
:class:`.QosPolicy` fields can be accessed, modified, queried and deleted in the same manner as any other InfiniSDK object:

.. code-block:: python

    >>> qos_policy.get_max_ops()
    1000
    >>> qos_policy.update_max_bps(100000000)
    >>> qos_policy.get_max_bps()
    100000000
    >>> from infinisdk import Q
    >>> print(', '.join([policy.get_name() for policy in system.qos_policies.find(Q.max_bps >= 1000).to_list()]))
    my_policy
    >>> qos_policy.delete()

Entities Assignment
-------------------
An assignment of a ``QosPolicy`` object to a pool or a dataset can be done in two ways.
The first one is by referencing the QoS policy object:

.. code-block:: python

    >>> qos_policy = system.qos_policies.create(type='volume', max_ops=1000, name='my_policy')
    >>> qos_policy.assign_entity(volume)

The second one is by referencing the entity object and calling :func:`assign_qos_policy <infinisdk.infinibox.volume.Volume.get_qos_policy>`.

A pool can be assigned to a 'pool_volume` QoS policy:

.. code-block:: python

    >>> pool_qos_policy = system.qos_policies.create(type='pool_volume', max_ops=10000, burst_enabled=False, name='vol_policy')
    >>> pool.assign_qos_policy(pool_qos_policy)
    >>> print(', '.join([policy.get_name() for policy in pool.get_qos_policies()]))
    vol_policy

Querying
--------
QoS Policy of a dataset can be retrieved by using the :func:`get_qos_policy <infinisdk.infinibox.volume.Volume.get_qos_policy>` method:

.. code-block:: python

    >>> print(volume.get_qos_policy().get_name())
    my_policy

A dataset can also have a shared QoS policy, from its pool:

.. code-block:: python

    >>> print(volume.get_qos_shared_policy().get_name())
    vol_policy

As a pool can have 2 policies, the :func:`get_qos_policy <infinisdk.infinibox.volume.Volume.get_qos_policy>` method is used.

Also, these convenience methods exist:

.. code-block:: python

    >>> print(pool.get_volume_qos_policy().get_name())
    vol_policy

It is possible to get all entities assigned to a QoS policy, using :func:`get_assigned_entities <infinisdk.infinibox.qos_policy.QosPolicy.get_assigned_entities>`:

.. code-block:: python

    >>> print(', '.join([entity.get_name() for entity in qos_policy.get_assigned_entities()]))
    my_volume

All entities assigned to QoS policies can be fetched as well:

.. code-block:: python

   >>> print(', '.join([entity.get_name() for entity in system.qos_policies.get_assigned_entities()]))
   my_volume, my_pool

Unassignment
------------
As with assignment, clearing QoS policies can also be done in two ways:

.. code-block:: python

    >>> volume.unassign_qos_policy(qos_policy)
    >>> volume.assign_qos_policy(qos_policy)
    >>> qos_policy.unassign_entity(volume)

For pools:

.. code-block:: python

    >>> pool.unassign_qos_policies()

Misc
----
Retrieving all existing QoS policies in the system:

.. code-block:: python

    >>> system.qos_policies.get_all()
    <Query /api/rest/qos/policies>

