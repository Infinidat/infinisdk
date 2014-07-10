System Compontents
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

For each Node, you can use the :meth:`.get_fc_ports` method to obtain the FC ports it contains. Each FC port is returned as a Python dictionary containing its attributes

.. code-block:: python

		>>> for node in system.components.nodes:
		...     for fc_port in node.get_fc_ports():
		...         if fc_port['link_state'] != 'Link Up':
		...             print('Port', fc_port['wwpn'], 'of', node, 'is down!')



