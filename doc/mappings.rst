Working with Hosts, Clusters and Mappings
=========================================

InfiniSDK provides an easy interface to query and manipulate volume mappings to hosts.

Creating Hosts
--------------

Creating hosts is the same like creating any other management object through InfiniSDK. Hosts are represented by the :class:`.Host` class:

.. code-block:: python

		>>> host = system.hosts.create(name='production01')
		>>> host # doctest: +ELLIPSIS
		<...:Host id=1009>
		>>> print(host.get_name())
		production01

Adding/Removing FC Ports
------------------------

Adding and removing FC ports can be done with :func:`infinisdk.infinibox.host.Host.add_port` and :func:`infinisdk.infinibox.host.Host.remove_port`. The address should be an instance of the ``infi.dtypes.wwn.WWN`` class to denote an FC address:

.. code-block:: python

                >>> from infi.dtypes.wwn import WWN
		>>> address = WWN('00:01:02:03:04:05:06:07')
		>>> host.add_port(address)
		>>> host.remove_port(address)

Adding/Removing iSCSI IQNs
--------------------------

Adding and removing iSCSI IQNs is done in a fashion similar to FC ports, only that the address in this case should be an instance of the ``infi.dtypes.iqn.iSCSIName class``:

.. code-block:: python

                >>> from infi.dtypes.iqn import make_iscsi_name
		>>> address = make_iscsi_name('iqn.1994-05.com.redhat:8f8dcc647276')
		>>> host.add_port(address)
		>>> host.remove_port(address)



Querying Host by a Defined Port
-------------------------------

You can quickly check if a system has a host :func:`system.hosts.get_host_id_by_initiator_address <infinisdk.infinibox.host.HostBinder.get_host_id_by_initiator_address>`, :func:`system.hosts.get_host_by_initiator_address <infinisdk.infinibox.host.HostBinder.get_host_by_initiator_address>` and :func:`system.hosts.has_registered_initiator_address <infinisdk.infinibox.host.HostBinder.has_registered_initiator_address>`:

.. code-block:: python

		>>> system.hosts.has_registered_initiator_address(address)
		False
		>>> host.add_port(address)
		>>> system.hosts.get_host_by_initiator_address(address) == host
		True


Mapping and Unmapping Volumes and Snapshots
-------------------------------------------

Given a volume object, we can easily map it to a host:

.. code-block:: python

		>>> lu = host.map_volume(volume)

The :class:`returned lu object <.LogicalUnit>` represents the volume mapping to the specific host, and it can be used to retrieve information about the mapping:

.. code-block:: python

		>>> print(int(lu))
		1

Unmapping can be done in several ways. The easiest would be to call :meth:`.Host.unmap_volume`:

.. code-block:: python

		>>> host.unmap_volume(volume)

Which can also receive a specific LUN to unmap:

.. code-block:: python

		>>> lu = host.map_volume(volume, lun=2)

		>>> host.unmap_volume(lun=2)

The LUN can also be deleted directly through its accessor object:

.. code-block:: python

		>>> lu = host.map_volume(volume)
		>>> lu.unmap()


Querying Volume Mappings
------------------------

Iterating over available mappings of a host is fairly simple:

.. code-block:: python

		>>> lu = host.map_volume(volume, lun=5)

		>>> host.get_luns() # doctest: +ELLIPSIS
		<LogicalUnitsContainer: [<LUN 5: <...:Host id=1009>-><...:Volume id=1008>>]>

		>>> for lun in host.get_luns():
		...     print("{} is mapped to {}".format(lun, lun.volume)) # doctest: +ELLIPSIS
		<LUN 5: <...:Host id=1009>-><...:Volume id=1008>> is mapped to <...:Volume id=1008>

There is also a shortcut to iterate over all mappings in the entire system:

.. code-block:: python

		>>> for lun in system.luns:
		...     print("{} belongs to {} and is mapped to {}".format(lun, lun.mapping_object, lun.volume)) # doctest: +ELLIPSIS
		<LUN 5: <...:Host id=1009>-><...:Volume id=1008>> belongs to <...:Host id=1009> and is mapped to <...:Volume id=1008>


Here is a code snippet to unmap all volumes in the system that contain 'to remove' in their names:

.. code-block:: python

		>>> import itertools

		>>> volume.update_name('this is a volume to remove')

		>>> for mapping_object in itertools.chain(system.host_clusters, system.hosts):
		...     for lun in mapping_object.get_luns():
		...         if 'to remove' in lun.volume.get_name():
		...             print("Unmapping", lun.volume)
		...             lun.unmap() # doctest: +ELLIPSIS
		Unmapping <...:Volume id=1008>


Of course there is a much more convenient shortcut for unmapping a volume from all hosts, using the :meth:`.Volume.unmap` shortcut:

.. code-block:: python

		>>> lu = host.map_volume(volume)
		>>> host.is_volume_mapped(volume)
		True
		>>> volume.unmap()
		>>> host.invalidate_cache()
		>>> host.is_volume_mapped(volume)
		False

Clusters and Hosts
------------------

Manipulating clusters is done with the :class:`infinisdk.infinibox.host_cluster.HostCluster` class:

.. code-block:: python

		>>> cluster = system.host_clusters.create()
		>>> cluster.add_host(host)

		>>> lu = cluster.map_volume(volume)

		>>> host.invalidate_cache()
		>>> [host_lu] = host.get_luns()

		>>> host_lu # doctest: +ELLIPSIS
		<LUN 11: <...:Host id=1009>-><...:Volume id=1008>>

		>>> host_lu.is_clustered()
		True

.. seealso::
    * :mod:`Host API documentation <infinisdk.infinibox.host>`
    * :mod:`Cluster API documentation <infinisdk.infinibox.host_cluster>`
