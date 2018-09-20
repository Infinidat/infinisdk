System Components
==================

InfiniSDK allows inspecting the hardware components in the system, and obtaining various attributes about them.

Nodes
-----

``system.components.nodes`` is a collection of :class:`infinisdk.infinibox.components.Node` objects:

.. code-block:: python

		>>> print('System has {} nodes'.format(system.components.nodes.count()))
		System has 3 nodes

Drives
------

InfiniSDK provides several ways of querying the system's drive information, ``system.components.enclosures`` and ``system.components.drives``. The first is intended for traversing the actual topology of the system through the :class:`.Enclosure` component, while the second is an aggregate of all drives in the system (:class:`.Drive` objects):

.. code-block:: python
       
       >>> for enclosure in system.components.enclosures:
       ...     for drive in enclosure.get_drives():
       ...         pass # <- do something with drive here

       >>> for drive in system.components.drives:
       ...     pass # <- do something with drive here

You can also query drives by their attributes, for instance by state:

.. code-block:: python
       
       >>> from infinisdk import Q
       >>> for drive in system.components.drives.find(Q.state != 'ACTIVE'):
       ...     print('Drive', drive, 'is not in ACTIVE!!!')




FC Ports
--------

For each Node, you can use the :meth:`.Node.get_fc_ports` method to obtain the FC ports it contains. Each FC port is returned as a Python dictionary containing its attributes

.. code-block:: python

		>>> for node in system.components.nodes:
		...     for fc_port in node.get_fc_ports():
		...         if not fc_port.is_link_up():
		...             print('Port', fc_port.get_field('wwpn'), 'of', node, 'is down!')


Use :meth:`.FcPort.disable` method to disable an FC port

.. code-block:: python

        >>> fc_port.disable()
        >>> fc_port.is_enabled()
        False

Use :meth:`.FcPort.enable` method to enable an FC port with a given role

.. code-block:: python

        >>> fc_port.enable(role='HARD_PORT')
        >>> fc_port.is_enabled()
        True


Services
--------

Use :meth:`.Node.get_service` to get a service by its name:

.. code-block:: python
       
       >>> node.get_service('mgmt') # doctest: +ELLIPSIS
       <...:Service id=system:0_rack:1_node:3_service:mgmt>

Or get a specific service type (core/mgmt):

.. code-block:: python
       
       >>> s = node.get_management_service()
       >>> s = node.get_core_service()



