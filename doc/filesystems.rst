Filesystems
===========

Creating a Filesystem
---------------------

Creating filesystems is done with the ``create`` method:

.. code-block:: python

		>>> fs = system.filesystems.create(pool=pool, name='my_fs')

.. note:: When a size isn't explicitly stated, a default of 1 GiB is used. You can also provide the size explicitly:

	  .. code-block:: python

			  >>> from capacity import GiB
			  >>> fs = system.filesystems.create(pool=pool, size=1*GiB)

It is also possible to create multiple filesystems with a single line, by calling :meth:`.create_many`:

.. code-block:: python

		>>> filesystems = system.filesystems.create_many(pool=pool, name='fs', count=5)
		>>> len(filesystems)
		5
		>>> for fs in filesystems:
		...     print(fs.get_name())
		fs_1
		fs_2
		fs_3
		fs_4
		fs_5


We can now access various attributes of the filesystem:

.. code-block:: python

		>>> print(fs.get_name())
		my_fs
		>>> fs.get_size()
		1*GB


Moving Between Pools
--------------------

Use :meth:`.Filesystem.move_pool` to move a filesystem between pools:

.. code-block:: python

		>>> new_pool = system.pools.create()
		>>> fs.move_pool(new_pool)


Resizing Filesystems
--------------------
Use :meth:`.Filesystem.resize` to resize the filesystem by the given delta:
.. code-block:: python

		>>> fs.resize(delta=2*GB)


Deleting Filesystems
--------------------

Deleting a filesystem is done with :meth:`.Filesystem.delete`:

.. code-block:: python

		>>> fs.delete()




Example: Deleting All Filesystems with Specific Name Prefix
-------------------------------------------------------

.. code-block:: python

		>>> for fs in system.filesystems:
		...     if fs.get_name(from_cache=True).startswith('prefix'):
		...         fs.delete()


.. seealso:: :mod:`Filesystem API documentation <infinisdk.infinibox.filesystem>`


Exports
=======

Creating a Filesystem Export
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A filesystem export is created with default settings and advanced setting. For a detailed documentation of these settings,
Read more `Here <https://support.infinidat.com/hc/en-us/articles/205711721-Exporting-a-filesystem>`_.

		>>> export = fs.add_export()

We can now access and modify various attributes of the export:

.. code-block:: python
		>>> from capacity import MiB
		>>> export.get_max_read()
		1*MB
		>>> export.update_max_read(2*MiB)
		>>> export.get_max_read()
		2*MB


Disabling an Export
-------------------

Following this operation, the filesystem is not accessible by the user. The export path is not deleted, and can be enabled.

.. code-block:: python

		>>> export.disable()
		>>> export.is_enabled()
		False


Enabling an Export
-------------------

.. code-block:: python

		>>> export.enable()
		>>> export.is_enabled()
		True


Querying for Filesystem Exports
-------------------------------

Like other infinidat collections, InfiniSDK provides iteration and filtering abilty for exports.

.. code-block:: python

		>>> system.exports.count()
		0

		>>> system.exports.to_list()
		[]


Deleting an Export
--------------------

Deleting an export is done with :meth:`.Export.delete`:

.. code-block:: python

		>>> export.delete()



Export Permissions
--------------------

| Export permissions can be modified with :meth:`.Export.update_permissions`.
| This method overrides current permissions.
|
| To preserve current permission settings, first use :meth:`.Export.get_permissions`, then update accordingly.

.. code-block:: python

		>>> permissions = export.get_permissions()
		>>> permissions
		[Munch({u'access': u'RW', u'no_root_squash': True, u'client': u'*'})]
		>>> export.update_permissions(permissions +
		...   [{'access': 'RO', 'client': '1.1.1.1', 'no_root_squash': True}])
		>>> export.get_permissions()
		[Munch({u'access': u'RW', u'no_root_squash': True, u'client': u'*'}),
		 Munch({u'access': u'RW', u'no_root_squash': True, u'client': u'1.1.1.1'})]
		>>> permissions.update_permissions([{'access': 'RW', 'client': '2.2.2.2', 'no_root_squash': True})
		[Munch({u'access': u'RW', u'no_root_squash': True, u'client': u'2.2.2.2'})]
