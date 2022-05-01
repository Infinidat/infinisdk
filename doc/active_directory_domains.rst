Active Directory Domains
=========================


Joining a Domain
----------------

Join a domain using the ``create`` method:

.. code-block:: python

        >>> system.active_directory_domains.create(domain=domain, preferred_ips=["196.0.0.0"], username=username, password=password)  # doctest: +SKIP

Leaving a Domain
----------------

Leave a domain using the ``leave`` method:

.. code-block:: python

        >>> system.active_directory_domains.leave(username=username, password=password)  # doctest: +SKIP
