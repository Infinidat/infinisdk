Events
======

InfiniSDK represents system events through the *system.events* collection, which contains :class:`.Event` objects. Querying system events can be done in several ways. We can, for instance, iterate over all events:

.. code-block:: python

		>>> for event in system.events:
		...     print(event, ":", event.get_code())
		<Event id=1000> : VOLUME_CREATED
		<Event id=1001> : VOLUME_DELETED
		<Event id=1002> : VOLUME_CREATED
		<Event id=1003> : VOLUME_DELETED
		<Event id=1004> : VOLUME_CREATED
		<Event id=1005> : VOLUME_DELETED
		

Sorting is determined by the system by default, but we can easily change that. For instance, we can order the events by descending id:

.. code-block:: python
		
		>>> for event in system.events.find().sort(-system.events.fields.id):
		...     print(event)
		<Event id=1005>
		<Event id=1004>
		<Event id=1003>
		<Event id=1002>
		<Event id=1001>
		<Event id=1000>

We can also combine this with filtering. The following example filters by specific event code:

.. code-block:: python

		>>> for event in system.events.find(code='VOLUME_CREATED').sort(-system.events.fields.id):
		...     print(event)
		<Event id=1004>
		<Event id=1002>
		<Event id=1000>

Example: Getting all Events Newer than a Specific Sequence Number
-----------------------------------------------------------------

.. code-block:: python

		>>> from infinisdk import Q
		>>> for e in system.events.find(Q.seq_num>=1004):
		...     print(e)
		<Event id=1004>
		<Event id=1005>
		
