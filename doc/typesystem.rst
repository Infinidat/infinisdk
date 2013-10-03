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
   
   .. automethod:: __getitem__(classname)


.. autoclass:: infinipy2.core.type_binder.TypeBinder
   :members:

   .. automethod:: __len__()

Querying, Filtering, Paging
~~~~~~~~~~~~~~~~~~~~~~~~~~~

One useful thing that we can do with type binders is finding objects (one or many at a time):

Finding objects (one or many at a time) is done by the :func:`.TypeBinder.find`:

.. code-block:: python

    # get the number of objects stored in the system
    >>> len(system.objects.filesystems)
    5

    # get all filesystems with composite predicate
    >>> matching = system.objects.filesystems.find(system.objects.filesystems.fields.quota>=2*GB)
    >>> len(matching)
    1
    
    # get a filesystem with id
    >>> [filesystem] = system.objects.filesystems.find(id=2)

    # get a filesystem with id
    >>> objs = Filesystem.find(system).only_fields(["quota"]).sort(-system.objects.filesystems.fields.quota)

Queries are lazy, they are only sent to the system in the beginning of the iteration, and possibly span multiple pages during iteration.

.. note:: The default sort is by ascending id. In any sort order that is not by id, there might be inconsistencies formed in the iteration when crossing page boundaries. This is because objects can get created/deleted between calls. Sorting by id solves it because ids are monotonously increasing, enabling us to resume iteration properly. 

You can always turn the lazy behavior into an eager iteration by constructing a list from the lazy query.

Getting Specific Objects
~~~~~~~~~~~~~~~~~~~~~~~~

You can also get specific objects using the type binders:

.. code-block:: python

   >>> from infinipy2.core.exceptions import ObjectNotFound
   >>> system.objects.filesystems.get(system.objects.filesystems.fields.name == "fs1")
   <Filesystem id=1>
   >>> try:
   ...     system.objects.filesystems.get(system.objects.filesystems.fields.name == "nonexisting")
   ... except ObjectNotFound:
   ...     pass
   >>> system.objects.filesystems.safe_get(system.objects.filesystems.fields.name == "nonexisting") is None
   True
   >>> system.objects.filesystems.choose(system.objects.filesystems.fields.quota > 2*TiB)
   <Filesystem id=1000>
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

These APIs always fetch the values live from the system's API. This may take a long time, especially in tight loops.

As an optimization (left to the user to decide), get_field and get_fields support the optional *from_cache* flag, fetching the last seen value (if available):

.. code-block:: python

    >>> sum_of_all_fs = sum(fs.get_field("quota", from_cache=True) for fs in system.objects.filesystems.find().only_fields(["quota"]))


Defining an Object Schema
-------------------------

Types in the system are classes deriving from :class:`the SystemObject class<.SystemObject>`. The fields a specific object exhibits are defined in the **FIELDS** class variable:

.. code-block:: python


  >>> from infinipy2.core import *
  >>> from capacity import *
  >>> import string

  >>> class Filesystem(SystemObject):
  ...     FIELDS = [
  ...        Field(name="id", mutable=False, forbidden=True, is_unique=True),
  ...        Field("name", type=TypeInfo(str, min_length=FROM_CONFIG("defaults.max...."), max_length=1000, charset=string.printable), mandatory=True),
  ...        Field(
  ...            "quota", type=TypeInfo(Capacity, min=0, max=TiB), api_name="quota_in_bytes",
  ...            translator=FunctionTranslator(to_api=lambda x: int(x // byte), from_api=lambda x: int(x) * bytes),
  ...            mandatory=True,
  ...          ),
  ...     ]

Binding Object Types to Systems
-------------------------------
**TODO**

Field Definitions
~~~~~~~~~~~~~~~~~

The **FIELDS** class member must be a list of :class:`.Field` objects.

.. autoclass:: infinipy2.core.field.Field
   :members:

.. note:: Some of the real object fields exposed by the system may be of no interest to the application, and thus don't have to be specified in the **FIELDS** section. We can get the value of these fields through our getters, and update them using the update methods, but other parts like creation logic or filtering will not perform any special treatment for those fields. We will not attempt to translate their name or special conversion of their values.

The "id" Field
~~~~~~~~~~~~~~

All objects must be uniquely identifiable in their system. Infinipy uses the ``id`` field to do this, and it assumes that every object declares this field. Its exact type or its real name in the system is left to the implementation.


Field Type
~~~~~~~~~~

Fields have types. The exact type and the domain/behavior of its values is determined by the **type** keyword. It can be either a simple type (like any built-in Python type), or an instance of the :class:`.TypeInfo` class.

The latter provides some more customization about the type constraints or attributes, like min/max constraints and more.

.. autoclass:: infinipy2.core.type_info.TypeInfo
   :members:


The extra information for the type is used for querying the abstraction layer for capabilities - not for enforcing the limits. The API layer will send illegal values if given by the user. 

.. note:: If an illegal value (especially a value of an invalid type) is given to a field requiring :ref:`translation <translation>`, the translation will be skipped and the value will be sent as is. This allows us to perform negative testing more easily.

.. note:: should also take care of autogenrating defaults.


Values Taken from Config
~~~~~~~~~~~~~~~~~~~~~~~~

In many places in the field definition block we can refer to config paths, enabling us to store defaults and similar elements in a single place. This is done with the :func:`.FROM_CONFIG` proxy.

.. autofunction:: infinipy2.core.proxies.FROM_CONFIG


Defaults, Mandatory Fields and System Defaults
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each field is either mandatory..., optional or forbidden to be given to the :func:`.create` method. This is of course pertaining to the system's definition of the API. Fields that are not given to the :func:`.create` method but are mandatory will be autogenerated by the abstraction layer.

In addition, fields can be immutable or mutable (this is unrelated to whether they are forbidden in creation).


Omitted Fields
++++++++++++++

Sometimes we may want to omit a certain required field(s), while still autogenerating the other required fields. For this, ``OMIT`` exists, and is used like so:

.. code-block:: python

   Filesystem.create(system, name=OMIT) #  will autogenerate quota and other required fields, but skip generating the name

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

    


Object Lifetime
---------------

Objects can be queried for attribute values, and can optionally be created and/or deleted.

Object Creation (where applicable)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creation is always done by the classmethod :func:`.create`. Its first argument (not including the class itself) is always a system instance. The following keyword arguments are names of fields and their values.

Below is an example of how to implement such a method:

.. code-block:: python

 >>> from infinipy2.core import SystemObject
 
 >>> class Filesystem(SystemObject):
 ...     FIELDS = [
 ...       #...
 ...     ]
 ...     @classmethod
 ...     def create(cls, system, **fields):
 ...         returned = system.api.post(fields)
 ...         return cls(system, returned["result"]["id"])


Object Deletion
~~~~~~~~~~~~~~~

Deletion is done with :func:`.delete`, and forced deletion is done with :func:`.purge`.


Object Updates
~~~~~~~~~~~~~~

Objects that support updates expose the :func:`.update_fields` and :func:`update_field`:

.. code-block:: python

    filesystem = ...
    filesystem.update_fields(quota=4*GB, name="new_name")
    filesystem.update_field("quota", 16*GB)

