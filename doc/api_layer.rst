The API Layer
=============

Infinipy contains an API abstraction layer intended to ease the process of talking to the Infinidat API protocol.

.. autoclass:: infinipy2.core.api.API
   :members:

The ``target`` argument must inherit (either through `abc registration <http://docs.python.org/2/library/abc.html#abc.ABCMeta.register>`_ or via actual inheritance) from the :class:`.APITarget` class.

.. autoclass:: infinipy2.core.api.APITarget
   :members:
