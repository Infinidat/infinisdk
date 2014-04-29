The API Layer
=============

Infinipy contains an API abstraction layer intended to ease the process of talking to the Infinidat API protocol.

.. automodule:: infinipy2.core.api

.. autoclass:: infinipy2.core.api.API
   :members:

The ``target`` argument must inherit (either through `abc registration <http://docs.python.org/2/library/abc.html#abc.ABCMeta.register>`_ or via actual inheritance) from the :class:`.APITarget` class.

.. autoclass:: infinipy2.core.api.APITarget
   :members:

API Paths
---------

When interacting with the API, you can specify your own absolute path, or a relative path (defaulting to ``/api/rest/...``):

.. code-block:: python

   >>> unused = system.api.get("system")
   >>> unused = system.api.get("/api/rest/system") # same

Authentication
--------------
*TBD*

Dangerous Operations
--------------------

Infinidat systems define several operations which are considered dangerous, needing specific approval from the user. In simple scenarios like GUI or even console UI this causes a prompt to the user asking him or her to confirm what is about to be done.

In scripting tasks this is less critical, and it is assumed that it is better to let the script run interrupted than to raise an exception in such cases. Infinipy, therefore, always sends commands as "approved".

You can easily override this behavior by entering the *unapproved* context:

.. code-block:: python

    >>> with system.api.get_unapproved_context(): #doctest: +IGNORE_EXCEPTION_DETAIL, +ELLIPSIS
    ...     system.objects.filesystems.get_by_id_lazy(1).update_field("quota", 3*GB) #doctest: +IGNORE_EXCEPTION_DETAIL, +ELLIPSIS
    Traceback (most recent call last):
       ...
    CommandNotApproved: ...



