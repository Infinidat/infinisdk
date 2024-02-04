Snapshot Policies
=================

This is a process that automates periodic creation of snapshots on any of the system's storage entities - filesystem, volume, and a consistency-group (CG). Snapshot policies define the rules for snapshot creation.

Creating a Policy
-----------------
A policy defines how and when to create snapshots. It contains a list of schedules which define when to create a snapshot.

To create a policy:

.. code-block:: python

        >>> policy1 = system.snapshot_policies.create()

An optional parameters of `name` and `suffix` can be passed in creation. The suffix is a string which will be added to the snapshots' names.

Creating a Schedule
-------------------
After creating a policy you can create a schedule for creating the snapshot:

.. code-block:: python

        >> from datetime import timedelta
        >> schedule1 = policy1.schedules.create(name="every3hours",interval=timedelta(seconds=7200),retention=timedelta(seconds=3600)) 

In this example a snapshot will be taken every 7200 seconds and be retained for 3600 seconds (after which it will be deleted). 

The default type of schedule is `periodic` but you can also specify `type=clock` to denote a specific day and time. To do that you need to specify 2 additional parameters: 
        1. `day_of_week` which can get string values of the days of the week ("sunday", "monday", etc.) or "all" for all the days in the week.
        2. `time_of_day` which denotes the time in the day to perform the snapshot operation.

.. code-block:: python

        >> from datetime import time
        >> schedule2 = policy1.schedules.create(name="every3hours",type="clock",day_of_week="sunday",time_of_day=time(20, 30, 10),retention=timedelta(seconds=3600)) # doctest: +SKIP

In this example the snapshot will be taken every Sunday at 20:30:10 (8 PM, 30 minutes, 10 seconds).

A schedule cannot be updated. To make changes the schedule should be deleted and a new one with the change should be created.
Each policy can have up to 8 schedules.

Assigning Policies to Datasets
------------------------------
Snapshot policies can be assigned to datasets (of type master and snapshot): volumes, filesystems and CGs.
This dataset then will be snapshoted according to the policy schedule.

.. code-block:: python

        >>> fs1 = system.filesystems.create(name="fs1", pool=pool)
        >>> policy1.assign_entity(entity=fs1)

To unassign an entity from a policy you need to pass the entity instance that you want to unassign:

.. code-block:: python

        >>> policy1.unassign_entity(entity=fs1)

To get all the assigned entities for a policy you can do: 

.. code-block:: python

        >>> policy1_entities = policy1.get_assigned_entities()

You can also pass either one or both of the desired page size and page number in case you have many entities:

.. code-block:: python

        >>> policy1_entities = policy1.get_assigned_entities(page_size=1, page=1)
