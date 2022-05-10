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


.. seealso:: :mod:`Volume API documentation <infinisdk.infinibox.volume>`
