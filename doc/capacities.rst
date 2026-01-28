System Capacity
===============

InfiniSDK allows inspecting the capacity parameters of the system.

``system.capacities`` is a container for the different system capacity attributes

.. code-block:: python

		>>> print('System has {} total physical capacity'.format(system.capacities.get_total_physical_capacity()))
		System has 0.11 PB total physical capacity

		>>> print('System has {} free physical capacity'.format(system.capacities.get_free_physical_capacity()))
		System has 70.06 TiB free physical capacity

		>>> print('System has {} total virtual capacity'.format(system.capacities.get_total_virtual_capacity()))
		System has 0.23 PiB total virtual capacity

		>>> print('System has {} free virtual capacity'.format(system.capacities.get_free_virtual_capacity()))
		System has 0.21 PiB free virtual capacity

                >>> print('System has {} total allocated physical capacity'.format(system.capacities.get_total_allocated_physical_capacity()))
                System has 28 TB total allocated physical capacity

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
                System has 0 total spare partitions

                >>> print('System has {} total spare capacity'.format(system.capacities.get_total_spare_capacity()))
                System has 0 bit total spare capacity

                >>> print('System has {} total zeros capacity'.format(system.capacities.get_total_zeros_capacity()))  
                System has 0.86 GiB total zeros capacity

                >>> print('System has {} total effective capacity'.format(system.capacities.get_total_host_written_data()))  
                System has 1.9 GB total effective capacity

                >>> print('System has {} total reducible data effective capacity'.format(system.capacities.get_total_reducible_host_written_data()))  
                System has 2.1 GB total reducible data effective capacity

                >>> print('System has {} total reducible data disk usage capacity'.format(system.capacities.get_total_reducible_data_disk_usage_capacity()))  
                System has 0.13 GiB total reducible data disk usage capacity

                >>> print('System has {} total reducible data reduction ratio'.format(system.capacities.get_total_reducible_data_reduction_ratio()))  
                System has 14.583961022795974 total reducible data reduction ratio

                >>> print('System has {}% total reducible data percents'.format(system.capacities.get_total_reducible_data_percents()))  
                System has 70% total reducible data percents

                >>> print('System has {} total non-reducible data effective capacity'.format(system.capacities.get_total_non_reducible_host_written_data()))  
                System has 256 KiB total non-reducible data effective capacity

                >>> print('System has {} total non-reducible data disk usage capacity'.format(system.capacities.get_total_non_reducible_data_disk_usage_capacity()))  
                System has 250 KiB total non-reducible data disk usage capacity

                >>> print('System has {} total non-reducible data reduction ratio'.format(system.capacities.get_total_non_reducible_data_reduction_ratio()))  
                System has 1.024 total non-reducible data reduction ratio

                >>> print('System has {}% total non-reducible data percents'.format(system.capacities.get_total_non_reducible_data_percents()))  
                System has 7% total non-reducible data percents
