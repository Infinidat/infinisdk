Efficient Querying
==================

The relationship with InfiniBox REST API
----------------------------------------

InfiniSDK translates the operations on collections and object into REST
API. If the script you write will handle a large set of objects, then it
is important to use the InfiniSDK in the correct way, so that the APIs
are as efficient as possible. Failure to do so, will cause your script
to run slowly and for the increased overhead on the InfiniBox system.

Your script will probably contain snippets such as

.. code-block:: python

   from infinisdk import InfiniBox,Q
   system = InfiniBox("systemname", auth=("user", "password"))
   system.login()

   for vol in system.volumes:
       print("Volume: {} is {}".format(vol.get_name(),vol.get_size()))

This will translate into a REST API request that returns **all** the
data for **all** the volumes and volume snapshots on the system. Perhaps
this is what you intend to do, perhaps not…

If you know in advance that your script only requires access to **some**
of the objects in the system, you can provide this information via
InfiniSDK to make the REST API more efficient.

Logging the REST API the script uses
------------------------------------

We recommend that you familiarize yourself with the InfiniBox REST API,
which will help you identify potential performance improvements as you
run scripts.

To see the API requests, use the following code snippet which adds a
hook when InfiniSDK executes a REST API request:

.. code-block:: python

   import gossip
   @gossip.register('infinidat.sdk.before_api_request',token='api_dump')
   def pre_api(request):
       print(f"Request: {request} {request.url}")

This snippet prints the API to the standard error (you can send it to a
log file as well), for example:

.. code-block:: python

   for vol in system.volumes:
       print(f"Volume: {vol.get_name()} is {vol.get_size()}")

.. code-block::

   Requst: <PreparedRequest [GET]> http://systemname:443/api/rest/volumes
   Volume: vol1 is 1 GB

You can see the request URL, which retrieves all the volumes and volume
snapshots.

Improvement #1: Always use the find() function when querying for objects
------------------------------------------------------------------------

The find() function, which is available for all InfiniBox objects,
allows you to control multiple aspects of the REST API that InfiniSDK
generates.

**Always** use this function when enumerating objects. For example:

.. code-block:: python

   for vol in system.volumes.find():
       print(f"Volume: {vol.get_name()} is {vol.get_size()}")

Improvement #2: Fetching necessary fields only
----------------------------------------------

By default, InfiniSDK will request the entire object from the InfiniBox
system, and cache all the fields retrieved in memory. Typically, the
objct may contain many fields which your script doesn’t need. Fetching
these fields will increase the overhead on the InfiniBox system, on the
network (because the JSON document is large) and increse the memory
footprint of your script.

It is recommended to retrieve and **only** the fields you need, by using
the ``only_fields`` function:

.. code-block:: python

   for vol in system.volumes.find().only_fields(["name","size"]):
       print(f"Volume: {vol.get_name()} is {vol.get_size()}")

.. code-block::

   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes?fields=id%2Csize%2Cname

Now the API request and response include the only the specific two
fields required (name and size).

Improvement #3: Fetching all necessary fields
---------------------------------------------

If you trim down the requests to include specific fields, it is
important to include **all** the fields your script needs. If you fail
to do so, your script will still function correctly since InfiniSDK will
issue subsequent requests to retrieve these missing fields, but the
operation will be **very** inefficiect. For example:

.. code-block:: python

   for vol in system.volumes.find().only_fields(["name"]):
       print(f"Volume: {vol.get_name()} is {vol.get_size()}")

.. code-block::

   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes?fields=id%2Cname
   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes/132?fields=size
   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes/19443830?fields=size
   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes/19443832?fields=size

As you can see, the initial request retrieves only the name for all the
volumes. Since the script then needs the volume name, InfiniSDK issues a
specific request for the name of each object, separately.

Avoid this as much as possible.

Improvement #4: Retrieve only necessary objects
-----------------------------------------------

If your script only requires a subset of objects, use the find()
function to filter just the objects as much as possible.

The simplest way to do this is to use the Q.field format. Here are some
examples:

.. code-block:: python

   from infinisdk import Q
   from capacity import *

   system.volumes.find(Q.provisioning=="THICK")
   system.volumes.find(Q.type!="SNAPSHOT")
   system.volumes.find(Q.name.like("Database"))
   system.volumes.find(Q.size>=100*GiB)
   system.volumes.find(Q.pool.in_(["gil-pool","chen-pool"]))

For example, if your script doesn’t need volume snapshots you can use
the filter ``Q.type!="SNAPSHOT"`` as a parameter to find():

.. code-block:: python

   for vol in system.volumes.find(Q.type!="SNAPSHOT").only_fields(["name","size"]):
       print(f"Volume: {vol.get_name()} is {vol.get_size()}")

.. code-block::

   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes?type=ne%3ASNAPSHOT&fields=id%2Csize%2Cname

Now the API request contains a filter the will refrain from retrieving
snapshots, instead of the following **inefficiect** code:

.. code-block:: python

   for vol in system.volumes.find().only_fields(["name","size","type"]):
       if (vol.get_type() != "SNAPSHOT"):
           print(f"Volume: {vol.get_name()} is {vol.get_size()}")

.. code-block::

   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes?fields=type%2Cid%2Csize%2Cname

If you need to filter according to multiple fields, add more filters to
the find() function.

For exameple, to list only volumes (no snapshots) whose name begins with
“Database” add the ``Q.name.like("Database")`` paramter after
``Q.type!="SNAPSHOT"``:

.. code-block:: python

   for vol in system.volumes.find(Q.type!="SNAPSHOT",Q.name.like("Database")).only_fields(["name","size"]):
       print(f"Volume: {vol.get_name()} is {vol.get_size()}")

.. code-block::

   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes?type=ne%3ASNAPSHOT&name=like%3ADatabase&fields=id%2Csize%2Cname

Improvement #5: Retrieve as many object with each API request as possible
-------------------------------------------------------------------------

InfiniBox REST API has built-in paging capabilities, which InfiniSDK
uses automatically. By default InfiniSDK uses a page size of 50, which
means every API request returns at most 50 objects. If the query you run
has more objcets InfiniSDK issues multiple API requests (each one
returns 50 objects) until all the list is exhaused.

Note: this is the default behavior, unless you add the page() function
as shown in the next improvement.

It is recommended to use larger page sizes: this will minimize the
communication and overhead, and has practically no downsides (unless you
retrieve large objects with many fields and text). For example:

.. code-block:: python

   for vol in system.volumes.find(Q.type!="SNAPSHOT").only_fields(["name","size"]).page_size(1000):
       print(f"Volume: {vol.get_name()} is {vol.get_size()}")

.. code-block::

   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes?type=ne%3ASNAPSHOT&fields=id%2Cname%2Csize&page=1&page_size=1000

The above retrieves 1000 volumes (or less if there are fewer volumes) in
a single API request.

Improvement #6: Retrieve the top-most objects
---------------------------------------------

Sometimes the script only needs the first (or last) objects based on
some order. For example, you might want to display the 5 oldest
snapshots of volume “Database1”.

Doing this efficiently requires the combination of the **sorting** and
**paging** capabilities in the REST API.

Use the sort() function to indicate the field(s) by which you want the
objects, the page_size() function to indicate how many objects you want,
and use the page() function to limit the retrival to one page. The above
example can be achieved thus:

.. code-block:: python

   for vol in system.volumes.find(Q.parent_id==1615).only_fields(["name","size"]).sort(Q.created_at).page_size(5).page(1):
       print(f"Volume: {vol.get_name()} is {vol.get_size()}")

.. code-block::

   Requst: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes?type=eq%3ASNAPSHOT&parent_id=eq%3A1615&fields=size%2Cname%2Cid&sort=created_at&page=1&page_size=5

The above example will use a single REST API request to retrieve 5
objects - the most **efficient** way to do that.

Note: paging in InfiniBox is limited to 1000 objects at most, so if you
need more you will need to repeat this with ``page(1)``, then
``page(2)``, etc.

Improvement #7: Retrieve a single object
----------------------------------------

If you know you’re going to get a single object, there is a quick and
simple way to do that, using the ``get()`` function. For example, to
find a volume by name:

.. code-block:: python

   system.volumes.get(Q.name=='my-volume-name')

.. code-block::

   Request: <PreparedRequest [GET]> https://systemname:443/api/rest/volumes?name=eq%3Amy-volume-name

This is essentially the same as ``find(<predicate>)[0]``, plus the
necessary exceptions if no objects meet the predicate or more than one
object does.
