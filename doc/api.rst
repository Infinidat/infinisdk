API Reference
=============

infinibox
~~~~~~~~~

.. automodule:: infinisdk.infinibox

.. autoclass:: infinisdk.infinibox.InfiniBox
   :members:

infinibox.api
~~~~~~~~~~~~~

``infinibox.api`` is the sub-object responsible for sending API requests to the system. It also holds the current authentication information for the session.

.. automodule:: infinisdk.core.api.api

.. autoclass:: API
   :members:

.. autoclass:: Response
   :members:

infinibox.volumes
~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.volume

.. autoclass:: VolumesBinder
   :members:

.. autoclass:: Volume
   :members:
   :inherited-members:

infinibox.pools
~~~~~~~~~~~~~~~

*infinibox.pools* is of type :class:`.PoolBinder` described below.


.. automodule:: infinisdk.infinibox.pool

.. autoclass:: PoolBinder
   :members:

.. autoclass:: Pool
   :members:
   :inherited-members:

infinibox.hosts
~~~~~~~~~~~~~~~

*infinibox.hosts* is of type :class:`.HostBinder` described below.

.. automodule:: infinisdk.infinibox.host

.. autoclass:: HostBinder
   :members:
   :inherited-members:

Individual host objects are of type :class:`.Host`:

.. autoclass:: Host
   :members:
   :inherited-members:

infinibox.clusters
~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.host_cluster

.. autoclass:: HostCluster
   :members:


infinibox.replicas
~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.replica

.. autoclass:: ReplicaBinder
   :members:

.. autoclass:: Replica
   :members:

infinibox.links
~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.link

.. autoclass:: Link
   :members:

infinibox.network_spaces
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: infinisdk.infinibox.network_space.NetworkSpace
   :members:


infinibox.events
~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.core.events

.. autoclass:: Event
   :members:

infinibox.users
~~~~~~~~~~~~~~~

.. autoclass:: infinisdk.infinibox.user.User
   :members:
   :inherited-members:

infinibox.ldap_configs
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.ldap_config

.. autoclass:: LDAPConfig
   :members:

infinibox.notification_targets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.notification_target

.. autoclass:: NotificationTarget
   :members:

infinibox.cons_groups
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.cons_group

.. autoclass:: ConsGroup
   :members:

infinibox.metrics
~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.metrics

.. autoclass:: Metrics
   :members:

.. autoclass:: Filter
   :members:

.. autoclass:: FilterField
   :members:

.. autoclass:: CollectorField
   :members:

.. autoclass:: Collector
   :members:

.. autoclass:: Sample
   :members:



infinibox.components
~~~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.components

.. autoclass:: Node
   :members:

.. autoclass:: Enclosure
   :members:

.. autoclass:: Drive
   :members:


Base Objects
~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.system_object

.. autoclass:: InfiniBoxObject
   :members:

Infinibox Utilities
~~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.lun

.. autoclass:: LogicalUnit
   :members:
   :special-members: __int__

.. automodule:: infinisdk.infinibox.scsi_serial

.. autoclass:: SCSISerial
   :members:


Core Facilities
~~~~~~~~~~~~~~~

.. automodule:: infinisdk.core.type_binder

.. autoclass:: infinisdk.core.type_binder.TypeBinder
  :members:

.. automodule:: infinisdk.core.system_object

.. autoclass:: infinisdk.core.system_object.SystemObject
  :members:
  :inherited-members:


.. autoclass:: infinisdk.core.object_query.ObjectQuery
  :members:

.. autofunction:: infinisdk.core.extensions.add_method

Exceptions
~~~~~~~~~~

.. automodule:: infinisdk.core.exceptions
 
.. autoclass:: infinisdk.core.exceptions.ObjectNotFound
.. autoclass:: infinisdk.core.exceptions.TooManyObjectsFound
