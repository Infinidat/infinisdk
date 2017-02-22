Events
======

InfiniSDK represents system events through the *system.events* collection, which contains :class:`.Event` objects. Querying system events can be done in several ways. We can, for instance, iterate over all events:

.. code-block:: python

		>>> for event in system.events:
		...     print(event) # doctest: +ELLIPSIS
		<...:Event id=1000, code=VOLUME_CREATED>
		<...:Event id=1001, code=VOLUME_DELETED>
		<...:Event id=1002, code=VOLUME_CREATED>
		<...:Event id=1003, code=VOLUME_DELETED>
		<...:Event id=1004, code=VOLUME_CREATED>
		<...:Event id=1005, code=VOLUME_DELETED>
		<...:Event id=1006, code=USER_LOGIN_SUCCESS>


Sorting is determined by the system by default, but we can easily change that. For instance, we can order the events by descending id:

.. code-block:: python

		>>> for event in system.events.find().sort(-system.events.fields.id):
		...     print(event) # doctest: +ELLIPSIS
		<...:Event id=1006, code=USER_LOGIN_SUCCESS>
		<...:Event id=1005, code=VOLUME_DELETED>
		<...:Event id=1004, code=VOLUME_CREATED>
		<...:Event id=1003, code=VOLUME_DELETED>
		<...:Event id=1002, code=VOLUME_CREATED>
		<...:Event id=1001, code=VOLUME_DELETED>
		<...:Event id=1000, code=VOLUME_CREATED>

We can also combine this with filtering. The following example filters by specific event code:

.. code-block:: python

		>>> for event in system.events.find(code='VOLUME_CREATED').sort(-system.events.fields.id):
		...     print(event) # doctest: +ELLIPSIS
		<...:Event id=1004, code=VOLUME_CREATED>
		<...:Event id=1002, code=VOLUME_CREATED>
		<...:Event id=1000, code=VOLUME_CREATED>

Example: Getting all Events Newer than a Specific Sequence Number
-----------------------------------------------------------------

.. code-block:: python

		>>> from infinisdk import Q
		>>> for e in system.events.find(Q.seq_num>=1004):
		...     print(e) # doctest: +ELLIPSIS
		<...:Event id=1004, code=VOLUME_CREATED>
		<...:Event id=1005, code=VOLUME_DELETED>
		<...:Event id=1006, code=USER_LOGIN_SUCCESS>

