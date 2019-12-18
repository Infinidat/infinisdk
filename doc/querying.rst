.. _querying:

Querying Objects
================

The InfiniBox API layer allows its users to query and sort objects according to various criteria. InfiniSDK offers a clean Pythonic syntax to perform such queries.

Querying All Objects
--------------------

Querying all objects can be done by iterating over the collection proxies (e.g. ``system.volumes``):

.. code-block:: python
		
		>>> system.volumes.count()
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
		>>> v # doctest: +ELLIPSIS
		<...:Volume id=1008>

Getting a Single Object
-----------------------

Getting a single object has an even easier shortcut -- ``get``, which assumes only one object is returned:

		>>> v = system.volumes.get(name='vol0')
		>>> v # doctest: +ELLIPSIS
		<...:Volume id=1008>

It will fail if either 0 or several objects are returned:

.. code-block:: python

		>>> system.volumes.get() # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		  ...
		TooManyObjectsFound

		>>> system.volumes.get(name='nonexistent') # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		  ...
		ObjectNotFound


There is also ``safe_get``, returning ``None`` instead of raising an exception if no object is found:

.. code-block:: python

		>>> system.volumes.safe_get(name='nonexistent') is None
		True

Advanced Queries
----------------

Object fields can be used to perform more complex queries, using operators. For instance, here is a query for all volumes whose name is not 'vol1'.

.. code-block:: python
		
		>>> for v in system.volumes.find(system.volumes.fields.name != 'vol1'):
		...     print(v.get_name())
		vol0
		vol2
		vol3
		vol4

The above code leverages Python's operator overloading to generate on-the-fly query filters. There is also a shorter syntax for writing the above piece of code, using the ``Q`` shortcut available from InfiniSDK:

.. code-block:: python

		>>> from infinisdk import Q

		>>> vols = system.volumes.find(Q.name != 'vol1')
		>>> len(vols)
		4

.. note:: ``Q.x != y`` is merely a shortcut for ``SomeObject.fields.x != y``, and provides no other additional functionality besides shortening the syntax.

.. note:: You can use the following operators ``==``, ``!=``, ``>``, ``>=``, ``<``, ``<=``, and also ``.in_(...)``, ``.not_in(...)``, ``.between(x, y)`` and ``.like("string")``. Not all operators are supported by all queries -- some limitations might apply.

And here is a query to find all volumes greater than 1 GiB in size:

.. code-block:: python
		
		>>> from capacity import GiB
		>>> system.volumes.find(system.volumes.fields.size > GiB).to_list()
		[]

.. seealso:: :ref:`capacities`

