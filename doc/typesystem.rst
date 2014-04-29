.. _typesystem:

Typesystem
==========

Overview
--------

This document describes the API provided by the object abstraction layer. Its goal is to provide a programmatic layer for interacting with system objects and collections.

Infinipy deals with logical objects reflected through the system API, called **system objects**, and represented as the :class:`.SystemObject` class. Such logical object classes are implemented as Python classes, and are instantiated by typesystem layer when wrapping API calls to the system.

Objects provide easy setters/getters for object attributes, as well as convenient wrappers for object creation and deletion (if supported). They also handle caching of attributes and other aspects of the reflection.

To "attach" objects to a specific system, another concept exists, which is the **object binder**. This is a relatively simple element responsible of "gluing" the objects to a specific system. Examples of such binders can be seen below as ``system.objects``, ``system.components``, etc.

Using System Objects
--------------------

The quickest way of accessing objects defined on a system is through ``system.objects``:

``system.objects`` is actually an instance of :class:`.TypeBinderContainer` and supports several convenience APIs for querying the supported types:

.. code-block:: python

   >>> system.objects["filesystems"]
   <izbox001.filesystems>
   >>> system.objects[Filesystem] # by class
   <izbox001.filesystems>

.. note:: ``system.objects`` is only one collection of type binders existing in the system. There's also ``system.components``, which bundles the physical components of a system. Each type binder is an instance of :class:`.TypeBinder`, and is a proxy that behaves like a collection, and enables several additional operations on the collection as a whole as we'll see later on.

.. autoclass:: infinipy2.core.type_binder_container.TypeBinderContainer
   :members:
   :special-members:

.. autoclass:: infinipy2.core.type_binder.TypeBinder
   :members:
   :special-members:

Querying, Filtering, Paging
~~~~~~~~~~~~~~~~~~~~~~~~~~~

One useful thing that we can do with type binders is finding objects (one or many at a time):

Finding objects (one or many at a time) is done by the :func:`.TypeBinder.find`:

.. code-block:: python

    # get the number of objects stored in the system
    >>> len(system.objects.filesystems)
    1

    # get all filesystems
    >>> unused = system.objects.filesystems.find()

    # ... or this:
    >>> unused = system.objects.filesystems.get_all()

    # get all filesystems with composite predicate
    >>> fs = system.objects.filesystems.create(name="some_name", quota=2.5*GB)
    >>> matching = system.objects.filesystems.find(system.objects.filesystems.fields.quota>=2*GB)
    >>> matching
    <Query /api/rest/filesystems?quota_in_bytes=ge%3A2000000000>
    >>> len(matching)
    1
    
    # get a filesystem with id
    >>> [filesystem] = system.objects.filesystems.find(id=2)

    # get a filesystem with id
    >>> objs = system.objects.filesystems.find().only_fields(["quota"]).sort(-system.objects.filesystems.fields.quota)

    # get all filesystems with page_size and/or page index
    >>> objs = system.objects.filesystems.find().page(1).page_size(100)

Note that once you request a specific page, the query is narrowed only to that page specifically:

.. code-block:: python

    >>> objs = system.components.find().page(5).page_size(10)
    >>> len(objs)
    10

Queries are lazy, they are only sent to the system in the beginning of the iteration, and possibly span multiple pages during iteration.

.. note:: The default sort is by ascending id. In any sort order that is not by id, there might be inconsistencies formed in the iteration when crossing page boundaries. This is because objects can get created/deleted between calls. Sorting by id solves it because ids are monotonously increasing, enabling us to resume iteration properly. 

You can always turn the lazy behavior into an eager iteration by constructing a list from the lazy query.

Getting Specific Objects
~~~~~~~~~~~~~~~~~~~~~~~~

You can also get specific objects using the type binders:

.. code-block:: python

   >>> from infinipy2.core.exceptions import ObjectNotFound
   
   >>> for fs in system.objects.filesystems:
   ...     unused = fs.id # do something with fs here

   >>> system.objects.filesystems.get(system.objects.filesystems.fields.name == "fs1")
   <Filesystem id=1>
   >>> try:
   ...     system.objects.filesystems.get(system.objects.filesystems.fields.name == "nonexisting")
   ...     assert False
   ... except ObjectNotFound:
   ...     pass
   >>> system.objects.filesystems.safe_get(system.objects.filesystems.fields.name == "nonexisting") is None
   True
   >>> fs = system.objects.filesystems.create(name="fs2", quota=2.5*TiB)
   >>> system.objects.filesystems.choose(system.objects.filesystems.fields.quota > 2*TiB) == fs
   True
   >>> system.objects.filesystems.safe_choose(system.objects.filesystems.fields.name == "nonexisting") is None
   True
   >>> system.objects.filesystems.count(system.objects.filesystems.fields.quota > 2*TiB)
   1

**TODO**: add ``create``

.. note:: For fixed collections, we assume that getting an object from the abstraction layer will always return the same instance. This is required for attaching properties/info to those objects. The other collections don't guarantee it, but can check equality/hashing of identical objects. 

Getting Object Attributes (Field Values)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Objects expose the :func:`.get_fields` and :func:`.get_field`:

.. code-block:: python

    >>> filesystem = system.objects.filesystems.get(name="fs1")
    >>> str(filesystem.get_fields(["name", "quota"])["name"])
    'fs1'
    >>> str(filesystem.get_field("name"))
    'fs1'

Getting all fields can be done without passing any arguments to :func:`.get_fields`:

.. code-block:: python

   >>> "name" in filesystem.get_fields()
   True
   >>> "quota" in filesystem.get_fields()
   True
   >>> "quota_in_bytes" in filesystem.get_fields()
   False


These APIs always fetch the values live from the system's API. This may take a long time, especially in tight loops.

As an optimization (left to the user to decide), get_field and get_fields support the optional *from_cache* flag, fetching the last seen value (if available):

.. code-block:: python

    >>> sum_of_all_fs = sum(fs.get_field("quota", from_cache=True) for fs in system.objects.filesystems.find().only_fields(["quota"]))

.. note:: by default, if the field is not in the cache, it will be fetched again. You can force only from cache by passing ``fetch_if_not_cached=False``

Checking if an Object Exists
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Objects support the :func:`.is_in_system` method for checking if they still exist in the system:

.. code-block:: python

   >>> fs = system.objects.filesystems.get_by_id_lazy(1023)
   >>> fs.is_in_system()
   False
   >>> fs = system.objects.filesystems.get_by_id_lazy(1)
   >>> fs.is_in_system()
   True

Creating Objects
~~~~~~~~~~~~~~~~

Creating an object is done by the **create** method:

.. code-block:: python

    >>> fs = system.objects.filesystems.create(name="test_fs", quota=1*GB)

.. note:: the **create** method above is a shortcut for the create method of the :class:`.Filesystem` class itself.

Object Deletion
~~~~~~~~~~~~~~~

Deletion is done with :func:`.delete`, and forced deletion is done with :func:`.purge`.

.. code-block:: python

 >>> fs = system.objects.filesystems.create(name="deleted_fs", quota=GB)
 >>> fs.delete()

.. code-block:: python

 >>> fs = system.objects.filesystems.create(name="deleted_fs", quota=GB)
 >>> fs.purge()

Object Updates
~~~~~~~~~~~~~~

Objects that support updates expose the :func:`.update_fields` and :func:`update_field`:

.. code-block:: python

    >>> filesystem = system.objects.filesystems.get_by_id_lazy(1)
    >>> filesystem.update_fields(quota=4*GB, name="new_name")
    >>> filesystem.update_field("quota", 3*GB)


Object Schemas
--------------

Types in the system are classes deriving from :class:`the SystemObject class<.SystemObject>`. The fields a specific object exhibits are defined in the **FIELDS** class variable:

.. code-block:: python


  >>> from infinipy2.core import *
  >>> from api_object_schema import *
  >>> from capacity import *
  >>> import string

  >>> class Filesystem(SystemObject):
  ...     FIELDS = [
  ...        Field(name="id", is_unique=True, is_identity=True),
  ...        Field("name", mutable=True, type=TypeInfo(str, min_length=FROM_CONFIG("defaults.max...."), max_length=1000, charset=string.printable), creation_parameter=True),
  ...        Field(
  ...            "quota", api_name="quota_in_bytes",
  ...            type=TypeInfo(Capacity, min=0, max=TiB, api_type=int, 
  ...                          translator=FunctionTranslator(to_api=lambda x: int(x // byte), from_api=lambda x: int(x) * bytes)),
  ...            creation_parameter=True, mutable=True
  ...          ),
  ...     ]

Field Definitions
~~~~~~~~~~~~~~~~~

The **FIELDS** class member must be a list of :class:`.Field` objects.

.. autoclass:: infinipy2.core.field.Field
   :members:

.. note:: Some of the real object fields exposed by the system may be of no interest to the application, and thus don't have to be specified in the **FIELDS** section. We can get the value of these fields through our getters, and update them using the update methods, but other parts like creation logic or filtering will not perform any special treatment for those fields. We will not attempt to translate their name or special conversion of their values.

Domains and Translation
~~~~~~~~~~~~~~~~~~~~~~~
.. _translation:

Field names and values exist in two domains - the API domain, which is the syntax recognized by the system's API service itself, and the translated domain, represented as Pythonic values by the abstraction layer. We'll be using those terms in the following discussion.

For instance, we would like the following code:

.. code-block:: python

    Filesystem.create(system, quota=2*GB, ...)

to be translated to the following JSON structure being posted:

.. code-block:: javascript

   {
     //...
     "quota_in_bytes": 2000000000,
     //...
   }

Here the API domain talks in ``quota_in_bytes`` which is an integer, while the translated domain talks in ``quota``, which is a `capacity unit <http://github.com/vmalloc/capacity>`_.


The "id" Field
~~~~~~~~~~~~~~

All objects must be uniquely identifiable in their system. Infinipy uses the ``id`` field to do this, and it assumes that every object declares this field. Its exact type or its real name in the system is left to the implementation.


Field Type
~~~~~~~~~~

Fields have types. The exact type and the domain/behavior of its values is determined by the **type** keyword. It can be either a simple type (like any built-in Python type), or an instance of the :class:`.TypeInfo` class.

The latter provides some more customization about the type constraints or attributes, like min/max constraints and more.


The extra information for the type is used for querying the abstraction layer for capabilities - not for enforcing the limits. The API layer will send illegal values if given by the user. 

.. note:: If an illegal value (especially a value of an invalid type) is given to a field requiring :ref:`translation <translation>`, the translation will be skipped and the value will be sent as is. This allows us to perform negative testing more easily.

.. note:: should also take care of autogenrating defaults.


Values Taken from Config
~~~~~~~~~~~~~~~~~~~~~~~~

In many places in the field definition block we can refer to config paths, enabling us to store defaults and similar elements in a single place. This is done with the :func:`.FROM_CONFIG` proxy.

.. autofunction:: infinipy2.core.proxies.FROM_CONFIG


Defaults, Mandatory Creation Fields and System Defaults
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each field which is a creation parameter is mandatory by default (meaning it is not optional for :func:`.create`). This can be changed by specifying the ``optional`` keyword argument as ``True``.

In addition, fields can be immutable or mutable (this is unrelated to whether they are forbidden in creation).


Omitted Fields
++++++++++++++

Sometimes we may want to omit a certain required field(s), while still autogenerating the other required fields. For this, ``OMIT`` exists, and is used like so:

.. code-block:: python

   from infinipy2.core.api import OMIT

   Filesystem.create(system, name=OMIT) #  will autogenerate quota and other required fields, but skip generating the name

