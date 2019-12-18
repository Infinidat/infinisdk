Using Object Metadata
=====================

InfiniBox allows a client script to assign metadata keys and values to various objects, and query them later.

Setting Metadata Keys
---------------------

.. code-block:: python

		>>> unused = volume.set_metadata('metadata_key', 'value!')

Getting Metadata Keys
---------------------

.. code-block:: python

		>>> print(volume.get_metadata_value('metadata_key'))
		value!

Getting nonexistent metadata, by default, raises an exception:

.. code-block:: python

		>>> volume.get_metadata_value('nonexisting') # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		  ...
		APICommandFailed: ...

You can provide defaults to be retrieved if metadata doesn't exist:

.. code-block:: python

		>>> volume.get_metadata_value('nonexisting', 2)
		2



Getting All Metadata Keys
-------------------------

Getting all metadata keys of specific object:

.. code-block:: python

		>>> for key, value in volume.get_all_metadata().items():
		...     print("Found key:", key, "with value:", value)
		Found key: metadata_key with value: value!

You can also get all metadata keys for all the object in the system:

.. code-block:: python

		>>> for object_metadata_item in volume.system.get_all_metadata():
		...     print("Found key: {key} with value: {value} for object id {object_id}".format(**object_metadata_item))
		Found key: metadata_key with value: value! for object id 1008


Deleting (Unsetting) Metadata
-----------------------------

.. code-block:: python

		>>> unused = volume.unset_metadata('metadata_key')
		>>> volume.get_all_metadata()
		{}

You can also clear all metadata related to a single object:

.. code-block:: python

		>>> volume.clear_metadata()


.. seealso:: :class:`.InfiniBoxObject`
