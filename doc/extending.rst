Extending InfiniSDK
===================

InfiniSDK focuses on providing the official InfiniBox API as provided to the customer by Infinidat. However, some uses may require accessing internal or custom APIs, or wrapping more complex sequences in convenient API calls. Examples of this can be technician APIs, development utilities, customer macros and more.

InfiniSDK provides a convenient extensibility mechanism to allow us to extend its behavior.

Extending Objects with Methods
------------------------------

A very common case is adding methods to InfiniSDK objects. Let's assume we want to add a method to an :class:`.InfiniBox` object, to get the location of the system from a global dictionary:

.. code-block:: python

   >>> s1 = InfiniBox(system1_address, auth = (username, password))
   >>> s2 = InfiniBox(system2_address, auth = (username, password))
   >>> _ = s1.login()
   >>> _ = s2.login()
   >>> locations = {s1: "upper floor", s2: "lower floor"}

By default, of course, we don't have such a mechanism:

.. code-block:: python

   >>> s1.get_location() # doctest: +IGNORE_EXCEPTION_DETAIL
   Traceback (most recent call last):
       ...
   AttributeError: ...


We head off to write our new method, and use :func:`infinisdk.core.extensions.add_method` to attach it to InfiniBox objects

.. code-block:: python

   >>> from infinisdk.core import extensions

   >>> @extensions.add_method(InfiniBox)
   ... def get_location(system):
   ...     return locations[system]

Now we can get the location safely:

.. code-block:: python

   >>> s1.get_location()
   'upper floor'
   >>> s2.get_location()
   'lower floor'
