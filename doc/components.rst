Components
==========

Infinipy provides reflection for physical system components (referred to here as *components*). Components are similar to logical objects :ref:`discussed earlier<typesystem>`, but they are slightly different:

1. They are cached by default -- getting the same component twice will return the very same Python object twice
2. They reside in ``system.components``, instead of ``system.objects``.

.. note:: The component *object* itself is cached. Actual data of this object is usually not cached.

Querying Components
-------------------

This is very similar to querying objects:

.. code-block:: python

    >>> encs = system.components.enclosures.find()
    >>> len(encs)
    8

    >>> len(system.components.enclosures.find(system.components.enclosures.fields.status != "OK"))
    0

Listing Component Types
-----------------------

There are several ways to obtain component types from the system:

.. code-block:: python

  >>> types = system.components.get_component_types()
  >>> system.components.types.Enclosure
  <class 'infinipy2.core.system_component.Enclosure'>


Retrieving Component Objects
----------------------------

Components collections are accessed using system.components.TypeName.
Getting component object(s) of a certain type is done using the :func:`.find` (see <link to system object find/queries > 
In addition it is possible to get a specific component using :func:`.get`, :func:`.safe_get` and :func:`.choose` 
    
.. code-block:: python

    drives = system.components.Drive.find(Drive.fields.status!='OK') # get all drives in system with a matching criteria
    drives = system.components.Drive.get_all() # get all drives in system (no interaction with system)
    drives = system.components.Drive.find(Drive.fields.status=='OK') # filter drives by status 
    drives = system.components.Drive.get(id=...) # get a specific drive by id  
    drives = system.components.Drive.choose() # get a random drive with match the criteria

The method :func:`.find` always generates a system API query and refreshes object information, thus allowing usage of cached data. for example:

.. code-block:: python

    # get all running drives
    drives =[drive for drive in system.comoponents.Drive.find().only_fields(["data"]) if drive.get_field("data", cached=True)['state'] == 'OK']
    
The method :func:`.get_all` returns all objects from cache without interacting with the system     


Component Objects
-----------------

All System components are derived from :class:`GenericSystemComponent<.GenericSystemComponent>` class. And should define a *_TYPE_NAME*. This is the type name as defined in the system.
It may also override the *_BINDER_CLASS* and *_BOUNDED_METHODS* 
*_BINDER_CLASS* should derive from :class:`ComponentTypeBinder>`

.. code-block:: python

  #>>> from infinipy2.core import GenericSystemComponent, GenericComponentBinder

  #>>> class Node(GenericSystemComponent):
  ...     FIELDS = []
  ...     _TYPE_NAME='node'
  ...     _BINDER_CLASS=NodeBinder
  ...     def is_master(self):
  ...         return node.get_index() = 1       
 
  #>>> class NodeBinder(GenericComponentBinder):
  ...     def get_master_node(self):
  ...         for node in self.get_all():
  ...            if node.is_master():
  ...                return node

Components Container
--------------------

Component type binders are attached to :class:`.ComponentBinderContainer` using :func:`.install` 
In addition the container will have additional shortcut methods for interacting with the entire components collection  

.. code-block:: python

    all_components = system.components.get_all() # get all components of all types
    specific_component = system.components.get_by_id() # get a specific component by id

Component hierarchy:
--------------------

System's components are arranged in an hierarchal structure, where :class:`The System Component<.SystemComponent>` is the root and represents the physical system
Each component is identified by *id*, *type*, *parent_id*, and *index*. 
While *id* is an unique identifier, *index* represents the physical location of a sub-component in relation to it's parent. 
Therefore components of the same type may have the same index (e.g. enclosure drives)

Component will expose the :func:`.get_parent` and :func:`.get_sub_components`:

.. code-block:: python

    drive.get_parent() # ==> enclosure object
    enclosure.get_sub_components() # ==> list of drives belonging to this enclosure   

.. note:: The list of sub components may be contain more than one type of components                
.. note:: Using the above methods does not require any interaction with the system and are much faster than using find  

Status and Alerts
-----------------

Component expose :func:`.get_fields` and :func:`.get_field` as described in <link to system object>  
In addition all components types will expose :func:`.get_status`, :func:`.get_alerts`, :func:`.get_data`

.. code-block:: python
   
   drive.get_alerts() # ==> list of alerts
   drive.get_status() # ==> component status (not state)
   drive.get_data() # ==> Additional component type specific data  

Some component types have states (not to be confused with status, which is an aggregation of alerts). 
These components types will have the additional :func:`.get_state` and possibly a state modifying methods

Installing Components
---------------------

All components in the system are installed at system creation.
Component types without pre-defined class are dynamically added based component type list, using the :class:`.GenericSystemComponent`
 
