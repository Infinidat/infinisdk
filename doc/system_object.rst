The InfiniBox Object
====================

Getting System Name and Serial Number
-------------------------------------

The system name and serial numbers can be obtained directly from the :class:`infinisdk.infinibox.InfiniBox` object:

.. code-block:: python

		>>> system_name = system.get_name()
		>>> system_serial = system.get_serial()

Getting the System Model Name
-----------------------------

The :meth:`infinisdk.infinibox.InfiniBox.get_model_name` method retrieves the model information, as reported by the system:

.. code-block:: python

		>>> isinstance(system.get_model_name(), str)
		True

.. seealso:: :class:`infinisdk.infinibox.InfiniBox`

Opening and Closing SSH Ports
-----------------------------

You can open/close the SSH ports of the system as well as querying its status by:

.. code-block:: python

        >>> system.open_ssh_ports()  # doctest: +SKIP
        >>> system.close_ssh_ports()  # doctest: +SKIP
        >>> system.get_ssh_ports_status()  # doctest: +SKIP
