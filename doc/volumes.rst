Volumes
=======

Creating and Modifying Volumes
------------------------------

Creating volumes is done with the ``create`` method:

.. code-block:: python

		>>> v = system.volumes.create(pool=pool, name='my_vol')

.. note:: When a size is not explicitly stated, a default of 1 GiB is used. You can also provide the size explicitly:

	  .. code-block:: python

			  >>> from capacity import GiB
			  >>> vol = system.volumes.create(pool=pool, size=1*GiB)

It is also possible to create multiple volumes with a single line, by calling :meth:`.create_many <.DatasetTypeBinder.create_many>`:

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

Volume Serials
--------------

InfiniSDK exposes the volume WWN serial number through a custom type, enabling you to parse it easier:

.. code-block:: python

        >>> serial = v.get_serial()
        >>> print(serial) # doctest: +ELLIPSIS
        742b0...
        >>> serial.ieee_company_id
        7613199
        >>> unused = serial.system_id  # doctest: +ELLIPSIS
        ...

.. seealso:: :class:`.SCSISerial`

Moving Between Pools
--------------------

Use :meth:`.Volume.move_pool` to move a volume between pools:

.. code-block:: python

		>>> new_pool = system.pools.create()
		>>> v.move_pool(new_pool)


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

.. ::

    .. code-block:: python

		>>> volume1 = system.filesystems.create(pool=pool)
		>>> volume2 = system.filesystems.create(pool=pool)
		>>> volume3 = system.filesystems.create(pool=pool)
		>>> v1 = system.filesystems.create(pool=pool)
		>>> v2 = system.filesystems.create(pool=pool)
		>>> v3 = system.filesystems.create(pool=pool)
		>>> f1 = system.filesystems.create(pool=pool)
		>>> f2 = system.filesystems.create(pool=pool)
		>>> f3 = system.filesystems.create(pool=pool)

Bulk Updating Volumes and Filesystems
-------------------------------------

The `bulk_update` method allows you to update the `ssa_express_enabled` field for multiple volumes or a combination of volumes and filesystems by passing a list of entities and the desired value.

**Updating Volumes**

>>> volumes = [volume1, volume2, volume3]  # List of volumes to update
>>> updated_volumes = system.volumes.bulk_update(volumes, ssa_express_enabled=True)

In this example, `volume1`, `volume2`, and `volume3` have their `ssa_express_enabled` field set to `True`.

**Updating Volumes and Filesystems**

>>> datasets = [v1, v2, v3, f1, f2, f3]
>>> updated_datasets = system.datasets.bulk_update(datasets, ssa_express_enabled=True)

In this example, both volumes (`v1`, `v2`, `v3`) and filesystems (`f1`, `f2`, `f3`) have their `ssa_express_enabled` field set to `True`.

**Note:** Currently, only the `ssa_express_enabled` field is supported for updates via this method.

.. seealso:: :mod:`Volume API documentation <infinisdk.infinibox.volume>`