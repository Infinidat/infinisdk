System Capacity
===============

InfiniSDK allows inspecting the capacity parameters of the system.

``system.capacities`` is a container for the different system capacity attributes

.. code-block:: python

		>>> print('System has {} total physical capacity'.format(system.capacities.get_total_physical_capacity()))
		System has 2.3 PiB total physical capacity

		>>> print('System has {} free physical capacity'.format(system.capacities.get_free_physical_capacity()))
		System has 2.3 PiB free physical capacity

		>>> print('System has {} total virtual capacity'.format(system.capacities.get_total_virtual_capacity()))
		System has 2.3 PiB total virtual capacity

		>>> print('System has {} free virtual capacity'.format(system.capacities.get_free_virtual_capacity()))
		System has 2.3 PiB free virtual capacity
