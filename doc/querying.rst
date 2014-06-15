.. _querying:

Querying Objects
================

The InfiniBox API layer allows its users to query and sort objects according to various criteria. InfiniSDK offers a clean Pythonic syntax to perform such queries

Querying All Objects
--------------------

Querying all objects can be done by iterating over the collection proxies (e.g. ``system.volumes``):

.. code-block:: python
		
		>>> len(system.volumes)
		5
		>>> for volume in system.volumes:
		...     print("Found volume:", volume.get_name())
		Found volume: vol0
		Found volume: vol1
		Found volume: vol2
		Found volume: vol3
		Found volume: vol4

.. note:: This is also equivalent to iterating over ``system.volumes.find()``


Querying by Fields
------------------

Querying by fields is relatively easy if you want a specific field value:

.. code-block:: python

		>>> [v] = system.volumes.find(name='vol0')
		>>> v
		<Volume id=1007>

Getting a Single Object
-----------------------

Getting a single object has an even easier shortcut -- ``get``, which assumes only one object is returned:

		>>> v = system.volumes.get(name='vol0')
		>>> v
		<Volume id=1007>

It will fail for either 0 or more than one are returned:

.. code-block:: python

		>>> system.volumes.get() # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		  ...
		TooManyObjectsFound

		>>> system.volumes.get(name='nonexistent') # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		  ...
		ObjectNotFound


There is also ``safe_get``, returning ``None`` instead of raising an exception if no object was found:

.. code-block:: python

		>>> system.volumes.safe_get(name='nonexistent') is None
		True

Advanced Queries
----------------

Object fields can be used to perform more complex queries, using operators. For instance, here is a query for all volumes which are not named 'vol1'

.. code-block:: python
		
		>>> for v in system.volumes.find(system.volumes.fields.name != 'vol1'):
		...     print(v.get_name())
		vol0
		vol2
		vol3
		vol4

And here is a query to find all volumes greater than 1 GiB in size:

.. code-block:: python
		
		>>> from capacity import GiB
		>>> list(system.volumes.find(system.volumes.fields.size > GiB))
		[]

.. seealso:: :ref:`capacities`
