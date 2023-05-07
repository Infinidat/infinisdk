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

                >>> print('System has {} total allocated physical capacity'.format(system.capacities.get_total_allocated_physical_capacity()))
                System has 0 bit total allocated physical capacity

                >>> print('System has {} dynamic spare drive cost'.format(system.capacities.get_dynamic_spare_drive_cost()))
                System has 0 dynamic spare drive cost

                >>> print('System has {} used dynamic spare partitions'.format(system.capacities.get_used_dynamic_spare_partitions()))
                System has 0 used dynamic spare partitions

                >>> print('System has {} used dynamic spare capacity'.format(system.capacities.get_used_dynamic_spare_capacity()))
                System has 0 bit used dynamic spare capacity

                >>> print('System has {} used spare partitions'.format(system.capacities.get_used_spare_partitions()))
                System has 0 used spare partitions

                >>> print('System has {} used spare capacity'.format(system.capacities.get_used_spare_capacity()))
                System has 0 bit used spare capacity

                >>> print('System has {} total spare partitions'.format(system.capacities.get_total_spare_partitions()))
                System has 3168 total spare partitions

                >>> print('System has {} total spare capacity'.format(system.capacities.get_total_spare_capacity()))
                System has 43.66 TiB total spare capacity
