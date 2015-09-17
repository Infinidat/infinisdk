.. _cons_groups:

Consistency Groups
==================

Creating Consistency Groups
---------------------------

.. code-block:: python
       
       >>> cg = system.cons_groups.create(pool=pool)

Adding Volumes to Consistency Groups
------------------------------------

.. code-block:: python
       
       >>> cg.add_member(volume)

Creating Snapshot Groups
------------------------

.. code-block:: python
       
       >>> sg = cg.create_snapshot()
       >>> sg.get_parent() == cg
       True

Restoring from Snapshot Group
-----------------------------

.. code-block:: python
       
       >>> cg.restore(sg)


