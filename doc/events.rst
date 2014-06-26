Events
======

InfiniSDK represents system events through the *system.events* collection, which contains :class:`.Event` objects. Querying system events can be done in several ways. We can, for instance, iterate over all events:

.. code-block:: python

		>>> for event in system.events:
		...     print(event, ":", event.get_code())
		<Event id=1000> : VOLUME_CREATE
		<Event id=1001> : VOLUME_DELETE
		<Event id=1002> : VOLUME_CREATE
		<Event id=1003> : VOLUME_DELETE
		<Event id=1004> : VOLUME_CREATE
		<Event id=1005> : VOLUME_DELETE
		

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

		>>> for event in system.events.find(code='VOLUME_CREATE').sort(-system.events.fields.id):
		...     print(event)
		<Event id=1004>
		<Event id=1002>
		<Event id=1000>

		

.. note:: Unlike regular InfiniSDK objects, event objects cache all of their properties and never fetch them again unless explicitly instructed to do so. See :ref:`caching` for more information.
