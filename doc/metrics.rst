Metrics
=======

InfiniSDK allows defining and sampling live metrics to monitor performance and other aspects of a running system.

Defining Filters
----------------

Creating a filter is done using ``system.metrics.create_filter``:

.. code-block:: python
       
       >>> filter = system.metrics.create_filter(protocol='NFS')

You can get the filter field details and the collector field details using ``filter_fields`` and ``collector_fields`` respectively:

.. code-block:: python

       >>> print(filter.filter_fields.pool_id.type)
       uint
       >>> print(filter.collector_fields.average_operation_size.unit)
       B
       >>> print(filter.collector_fields.throughput.unit)
       B/Sec

Creating a Collector and Polling Data
-------------------------------------

.. code-block:: python
       
       >>> collector = filter.create_collector(collected_fields=['ops'])
       >>> sample = collector.get_sample()
       >>> sample.value
       0

If your collector collects multiple fields, you can access them through the ``values`` munch:

.. code-block:: python
       
       >>> sample.values.ops
       True

You can also iterate using the :func:`iter_samples <infinisdk.infinibox.metrics.Collector.iter_samples>` method:

.. code-block:: python
       
       >>> for index, sample in enumerate(collector.iter_samples()):
       ...     # ...
       ...     break
       


.. seealso:: :class:`.infinibox.metrics.Metrics`
