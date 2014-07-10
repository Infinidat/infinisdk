Volumes
=======

Creating and Modifying Volumes
------------------------------

Creating volumes is done with the ``create`` method:

.. code-block:: python

		>>> v = system.volumes.create(pool=pool, name='my_vol')

.. note:: When a size isn't explicitly stated, a default of 1 GiB is used. You can also provide the size explicitly:

	  .. code-block:: python

			  >>> from capacity import GiB
			  >>> vol = system.volumes.create(pool=pool, size=1*GiB)

It is also possible to create multiple volumes with a single line, by calling :meth:`.create_many`:

.. code-block:: python

		>>> vols = system.volumes.create_many(pool=pool, name='vol', count=5)
		>>> len(vols)
		5
		>>> for vol in vols:
		...     print(vol.get_name())
		vol_1
		vol_2
		vol_3
		vol_4
		vol_5


We can now access various attributes of the volume:

.. code-block:: python

		>>> print(v.get_name())
		my_vol
		>>> v.get_size()
		1*GB

Deleting Volumes
----------------

Deleting a volume is done with :meth:`.Volume.delete`:

.. code-block:: python

		>>> v.delete()



Example: Deleting All Volumes with Specific Name Prefix
-------------------------------------------------------

.. code-block:: python

		>>> for volume in system.volumes:
		...     if volume.get_name(from_cache=True).startswith('prefix'):
		...         volume.delete()


.. seealso:: :mod:`Volume API documentation <infinisdk.infinibox.volume>`
