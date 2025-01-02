Snapshots
=========

Creating Snapshots
-----------------------------

Use the :meth:`.create_snapshot <.Dataset.create_snapshot>`

.. code-block:: python

		>>> snap = volume.create_snapshot()
		>>> snap_of_snap = snap.create_snapshot()

Creating Group Snapshots
------------------------

You can create a group of snapshots (not to be confused with :ref:`Consistency Groups <cons_groups>`) using :meth:`.create_group_snapshot`:

.. code-block:: python

       >>> v1, v2, v3 = volumes = [system.volumes.create(pool=pool) for i in range(3)]
       >>> s1, s2, s3 = system.volumes.create_group_snapshot(volumes)


Querying Snapshots
------------------

The parent of a snapshot is accessed through the :meth:`snap.get_parent/vol.get_parent <.Volume.get_parent>` method:

.. code-block:: python

		>>> snap.get_parent() == volume
		True

		>>> volume.get_parent() is None
		True

You can inspect the snapshot's creation time:

.. code-block:: python

		>>> creation_time = snap.get_creation_time()
		>>> delta = current_time - creation_time
		>>> delta.days
		15

.. note:: Time is represented in InfiniSDK with `Arrow objects <https://arrow.readthedocs.io/en/latest>`_. See the `relevant documentation <https://arrow.readthedocs.io/en/latest/#user-s-guide>`_ for more details on how to use and manipulate these values.



Example: Deleting Snapshots by Creation Time
--------------------------------------------

.. code-block:: python

		>>> cutoff = current_time.shift(days=-10)
		>>> for snapshot in system.volumes.find(system.volumes.fields.created_at < cutoff, parent_id=volume.id):
		...     print("Deleting snapshot with id:", snapshot.id)
		...     snapshot.delete()  # doctest: +ELLIPSIS
		Deleting snapshot with id: ...



Promoting a Snapshot
---------------------
Promoting a snapshot will allow admins to "convert" the snapshot into a standalone dataset, in order
to move it to a separate pool than the original volume or replicate it to another InfiniBox system.  

After promoting a snapshot a new "Master" snapshot will be created and the old snapshot will become an Internal Dataset.
Internal Datasets are the leftovers of the promote snapshot action, it is needed by the system and it will be "garbage collected" at some point by the system.
Users can only view its contents since an internal dataset still occupies some storage space.

.. note:: At the moment only volumes are supported.


Promoting a snapshot is done with :meth:`.Volume.promote_snapshot`

.. code-block:: python

		>>> snapshot = volume.create_snapshot()
		>>> snapshot.get_type()
		'SNAPSHOT'

		>>> promoted_snapshot = snapshot.promote_snapshot()
		>>> promoted_snapshot.get_type()
		'MASTER'



Promoting a CG Snapshot
------------------------
Promoting a CG snapshot will promote all the volumes that are members of the CG, 
it is done by calling :meth:`.ConsGroup.promote_snapshot`

.. code-block:: python

		>>> cg_snapshot = cg.create_snapshot()
		>>> cg_snapshot.get_type()
		'SNAPSHOT'

		>>> # all the volumes in the snapshot are of type snapshot
		>>> cg_snapshot_volume_types = [member.get_type() for member in cg_snapshot.get_members().to_list()]
		>>> all(volume_type == 'SNAPSHOT' for volume_type in cg_snapshot_volume_types)
		True

		>>> promoted_cg_snapshot = cg_snapshot.promote_snapshot()
		>>> promoted_cg_snapshot.get_type()
		'MASTER'

		>>> # all the volumes in the promoted snapshot are of type master
		>>> promoted_cg_snapshot_volume_types = [member.get_type() for member in promoted_cg_snapshot.get_members().to_list()]
		>>> all(volume_type == 'MASTER' for volume_type in promoted_cg_snapshot_volume_types)
		True



Getting all the Internal Datasets or Volumes
---------------------------------------------
In order to get all the data of Internal Datasets in our system we use ``infinibox.datasets.get_all_internals()``

For all the Internal Volumes in our system we use ``infinibox.volumes.get_all_internals()``

We can filter the results by internal_type (Master or Snapshot).

.. code-block:: python

		>>> all_internal_datasets = system.datasets.get_all_internals()

		>>> all_internal_volumes_type_master = system.volumes.get_all_internals(internal_type='master')
		>>> all_internal_volumes_type_snapshot = system.volumes.get_all_internals(internal_type='snapshot')


You can also pass a page number and/or the page size:

.. code-block:: python

		>>> all_internal_datasets = system.datasets.get_all_internals(page=1, page_size=20)
		>>> all_internal_volumes = system.volumes.get_all_internals(page=1, page_size=20)


Getting Internal Volumes of a specific Volume
------------------------------------------------
We can get the Internal Volumes of a specific Volume by calling :meth:`.Volume.get_all_internals`

.. code-block:: python

		>>> volume_internal_volumes = volume.get_all_internals()
		

You can also pass a page number and/or the page size:

.. code-block:: python

		>>> volume_internal_volumes = volume.get_all_internals(page=1, page_size=20)


.. note:: Retrieving the Internal Datasets of another Internal Dataset is not supported via InfiniSDK.



.. seealso:: :mod:`Volume API documentation <infinisdk.infinibox.volume>`
