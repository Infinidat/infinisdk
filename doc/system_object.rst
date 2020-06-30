The InfiniBox Object
====================

Getting System Name and Serial Number
-------------------------------------

The system name and serial numbers can be obtained directly from the :class:`.InfiniBox` object:

.. code-block:: python

		>>> system_name = system.get_name()
		>>> system_serial = system.get_serial()

Getting the System Model Name
-----------------------------

The :meth:`.InfiniBox.get_model_name` method retrieves the model information, as reported by the system:

.. code-block:: python

		>>> isinstance(system.get_model_name(), str)
		True

.. seealso:: :class:`.InfiniBox`



