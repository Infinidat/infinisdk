Manipulating Snapshots and Clones
=================================

Creating Snapshots and Clones
-----------------------------

Use the :meth:`.create_snapshot` and :meth:`.create_clone` methods:

.. code-block:: python
	
		>>> snap = volume.create_snapshot()
		>>> snap.id
		1008
		>>> clone = snap.create_clone()
		>>> clone.id
		1009

Querying Snapshots and Clones
-----------------------------

The parent of a snapshot or a clone is accessed through the :meth:`.get_parent` method:

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

.. note:: times are represented as `Arrow objects <http://crsmithdev.com/arrow/>`_. See the `relevant documentation <http://crsmithdev.com/arrow/#user-s-guide>`_ for more details on how to use and manipulate these values.



Example: Deleting Snapshots by Creation Time
--------------------------------------------

.. code-block:: python
		
		>>> cutoff = current_time.replace(days=-10)
		>>> for snapshot in system.volumes.find(system.volumes.fields.created_at < cutoff, parent_id=volume.id):
		...     print("Deleting snapshot with id:", snapshot.id)
		...     snapshot.delete()
		Deleting snapshot with id: 1008


.. seealso:: :mod:`Volume API documentation <infinisdk.infinibox.volume>`
