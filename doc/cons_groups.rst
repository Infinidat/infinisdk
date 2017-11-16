.. _cons_groups:

Consistency Groups
==================

InfiniSDK allows creating, adding/removing members and manipulating consistency groups.

Creating Consistency Groups
---------------------------

Consistency groups are created just like all InfiniSDK objects, through the ``create`` method:

.. code-block:: python
       
       >>> cg = system.cons_groups.create(pool=pool)

Adding and Removing Volumes
---------------------------

Use the :meth:`.ConsGroup.add_member` method to add members to a consistency group:

.. code-block:: python
       
       >>> cg.add_member(volume)

Use the :meth:`.ConsGroup.remove_member` method to remove members from a consistency group:

.. code-block:: python
       
       >>> cg.remove_member(volume)

Creating Snapshot Groups
------------------------

You can create a snapshot group from a consistency group through the :meth:`.ConsGroup.create_snapshot` method:

.. code-block:: python
       
       >>> cg.add_member(volume) # snap group creation is not allowed for empty CGs
       >>> sg = cg.create_snapshot()
       >>> sg.get_parent() == cg
       True

Restoring from Snapshot Group
-----------------------------

Restoring a snapshot group is done with the :meth:`.ConsGroup.restore` method:

.. code-block:: python
       
       >>> cg.restore(sg)


Deleting Consistency Groups
---------------------------

Deleting consistency groups is done through :meth:`.ConsGroup.delete`:

.. code-block:: python
       
       >>> sg.delete()
       >>> cg.delete()
