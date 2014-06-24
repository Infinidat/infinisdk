Volumes
=======

Creating and Modifying Volumes
------------------------------

Creating volumes is done with the ``create`` method:

.. code-block:: python

		>>> v = system.volumes.create(pool=pool, name='my_vol')

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

.. note:: :meth:`.Volume.delete` *only attempts to delete the volume*. In case more cleanup is needed (like unmapping from hosts), it will fail. For this, you can use the :meth:`.Volume.purge` method.




Example: Deleting All Volumes with Specific Name Prefix
-------------------------------------------------------

.. code-block:: python

		>>> for volume in system.volumes:
		...     if volume.get_name(use_cached=True).startswith('prefix'):
		...         volume.purge()


