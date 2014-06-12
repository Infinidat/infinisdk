Example Usage
=============

Deleting All Volumes with Specific Name Prefix
----------------------------------------------

.. code-block:: python

		>>> for volume in system.volumes:
		...     if volume.get_name(use_cached=True).startswith('prefix'):
		...         volume.purge()

