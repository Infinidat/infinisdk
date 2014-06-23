Working with Hosts, Clusters and Mappings
=========================================

InfiniSDK provides an easy interface to query and manipulate volume mappings to hosts. 

Creating Hosts
--------------

Creating hosts is the same like creating any other management object through InfiniSDK. Hosts are represented by the :class:`.Host` class:

.. code-block:: python

		>>> host = system.hosts.create(name='production01')
		>>> host
		<Host id=1008>
		>>> print(host.get_name())
		production01

Mapping and Unmapping Volumes and Snapshots
-------------------------------------------

Given a volume object, we can easily map it to a host:

.. code-block:: python

		>>> lu = host.map_volume(volume)

The :class:`returned lu object <.LogicalUnit>` represents the volume mapping to the specific host, and it can be used to retrieve information about the mapping:

.. code-block:: python

		>>> print(int(lu))
		1




Querying Volume Mappings
------------------------

