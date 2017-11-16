Network Configuration
=====================

Network Spaces
--------------

NAS, iSCSI, external replication and other network-related features require a configured *network space* to operate. A network space defines a set of configured IP addresses, as well as additional network-related configuration, with which the system can operate.

Creating Network Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Network spaces are defined on top of *network interfaces*, which can be created using ``system.network_interfaces.create``:


.. code-block:: python

       >>> interfaces = []
       >>> for node in system.components.nodes:
       ...     interfaces.append(
       ...         system.network_interfaces.create(node=node, ports=['eth-data1'])
       ...     )


Creating Network Spaces
~~~~~~~~~~~~~~~~~~~~~~~

Once the network interfaces are defined, creating a network space can be done via ``system.network_spaces.create``:

.. code-block:: python

       >>> interfaes = []
       >>> netspace = system.network_spaces.create(
       ...     name='ns1',
       ...     interfaces=interfaces,
       ...     service='RMR_SERVICE',
       ...     mtu=9000,
       ...     network_config={
       ...       'netmask': 19,
       ...       'network': '192.168.0.0',
       ...       'default_gateway': '192.168.1.1',
       ...     },
       ... )

Setting Network Space Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some network space types can receive additional configuration options through *properties*. These can be specified during network space creation through the ``properties`` parameter, and updated through ``update_properties``:

.. code-block:: python

       netspace = system.network_spaces.create(..., properties: {'is_async_only': True})
       ...
       netspace.update_properties({
         'is_async_only': False,
       })


.. seealso:: For more information regarding network space properties and their meaning, please refer to the official InfiniBox API documentation
