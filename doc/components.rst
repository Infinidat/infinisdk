System Components
==================

InfiniSDK allows inspecting the hardware components in the system, and obtaining various attributes about them.

Nodes
-----

``system.components.nodes`` is a collection of :class:`infinisdk.infinibox.components.Node` objects:

.. code-block:: python

		>>> print('System has {0} nodes'.format(len(system.components.nodes)))
		System has 3 nodes

FC Ports
--------

For each Node, you can use the :meth:`.Node.get_fc_ports` method to obtain the FC ports it contains. Each FC port is returned as a Python dictionary containing its attributes

.. code-block:: python

		>>> for node in system.components.nodes:
		...     for fc_port in node.get_fc_ports():
		...         if not fc_port.is_link_up():
		...             print('Port', fc_port.get_field('wwpn'), 'of', node, 'is down!')


Services
--------

Use :meth:`.Node.get_service` to get a service by its name:

.. code-block:: python
       
       >>> node.get_service('mgmt')
       <Service id=system:0_rack:1_node:3_service:mgmt>

Or get a specific service type (core/mgmt):

.. code-block:: python
       
       >>> s = node.get_management_service()
       >>> s = node.get_core_service()



