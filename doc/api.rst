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

.. automodule:: infinisdk.infinibox.pool

.. autoclass:: Pool
   :members:
   :inherited-members:

infinibox.hosts
~~~~~~~~~~~~~~~

*infinibox.hosts* is of type :class:`.HostBinder` described below.

.. automodule:: infinisdk.infinibox.host

.. autoclass:: HostBinder
   :members:

Individual host objects are of type :class:`.Host`:

.. autoclass:: Host
   :members:
   :inherited-members:

infinibox.clusters
~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.cluster

.. autoclass:: Cluster
   :members:
   :inherited-members:

infinibox.events
~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.core.events

.. autoclass:: Event
   :members:

infinibox.components
~~~~~~~~~~~~~~~~~~~~

.. automodule:: infinisdk.infinibox.components

.. autoclass:: Node
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



Core Objects
~~~~~~~~~~~~

.. automodule:: infinisdk.core.system_object

.. autoclass:: infinisdk.core.system_object.SystemObject
  :members:

