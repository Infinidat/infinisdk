Metrics
=======

InfiniSDK allows defining and sampling live metrics to monitor performance and other aspects of a running system.

Defining Filters
----------------

Creating a filter is done using ``system.metrics.create_filter``:

.. code-block:: python
       
       >>> filter = system.metrics.create_filter(protocol='NFS')

You can get the available fields and values for creation with :meth:`.Metrics.get_available_fields`:

.. code-block:: python
       
       >>> for field in system.metrics.get_available_fields():
       ...     unused = field.name
       ...     unused = field.values

You can get the filter field details and the collector field details using ``filter_fields`` and ``collector_fields`` respectively:

.. code-block:: python

       >>> print(filter.filter_fields.pool_id.type)
       uint
       >>> print(filter.collector_fields.average_operation_size.unit)
       B
       >>> print(filter.collector_fields.throughput.unit)
       B/Sec

Updating a filter is done with the :meth:`.Filter.update` method:

.. code-block:: python
       
       >>> filter.update(operation_type='commit')

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

Getting the samples currently pending in the collector can be done by :func:`get_samples <infinisdk.infinibox.metrics.Collector.get_samples>`, or if multiple collectors are needed :func:`get_samples <infinisdk.infinibox.metrics.Metrics.get_samples>`:

.. code-block:: python
       
       >>> samples = system.metrics.get_samples([collector]
       >>> samples = collector.get_samples()

You can also iterate using the :func:`iter_samples <infinisdk.infinibox.metrics.Collector.iter_samples>` method:

.. code-block:: python
       
       >>> for index, sample in enumerate(collector.iter_samples()):
       ...     # ...
       ...     break

The samples returned are actually :class:`infinisdk.infinibox.metrics.Sample` objects that represent the data points collected.       


.. seealso:: :class:`.infinibox.metrics.Metrics`
