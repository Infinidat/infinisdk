Cookbook
========

Below are several common tasks and how to accomplish them using InfiniSDK.

Objects
-------

Determining if an object is of a certain type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
       
       >>> assert isinstance(pool, system.pools.object_type)
       >>> assert not isinstance(pool, system.volumes.object_type)

