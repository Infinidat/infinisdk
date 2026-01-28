Active Directory Domains
=========================

Joining a Domain
----------------

Join a domain using the ``join`` method:

.. code-block:: python

        >>> system.active_directory_domains.join(
        ...     domain=domain,
        ...     preferred_ips=["196.0.0.0"],
        ...     username=username,
        ...     password=password
        ... )  # doctest: +SKIP

.. note::

   From version 8.1 onwards, the ``preferred_ips`` field is not mandatory.
   You can omit it if not required. It can accept the following:

   - ``None``
   - An empty list
   - A list of IP addresses
   - A list of domain names
   - A mix of both IP addresses and domain names

.. code-block:: python

        >>> system.active_directory_domains.join(
        ...     domain=domain,
        ...     username=username,
        ...     password=password
        ... )  # doctest: +SKIP

Leaving a Domain
----------------

Leave a domain using the ``leave`` method:

.. code-block:: python

        >>> system.active_directory_domains.leave(
        ...     username=username,
        ...     password=password
        ... )  # doctest: +SKIP
