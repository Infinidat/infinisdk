import random
from .exceptions import ObjectNotFound, TooManyObjectsFound
from .utils import deprecated


class TypeBinder(object):
    """
    Binds a specific type to a system.
    """

    def __init__(self, object_type, system):
        super(TypeBinder, self).__init__()
        self.object_type = object_type
        self.system = system

    def create(self, *args, **kwargs):
        """
        Creats an object on the system
        """
        return self.object_type.create(self.system, *args, **kwargs)

    @property
    def fields(self):
        return self.object_type.fields

    def get_mutable_fields(self):
        """Returns a list of all mutable fields for this object type
        """
        return [f for f in self.fields if f.mutable]

    def is_supported(self):
        return self.object_type.is_supported(self.system)

    def find(self, *predicates, **kw):
        """Queries objects according to predicates. Can receive arguments in two possible forms:

        1. Direct keyword arguments, for filtering for equality::

            system.volumes.find(size=GiB)

        2. Complex predicates, using the comparators::

            system.volumes.find(system.volumes.fields.size > GiB)
            system.volumes.find(Q.name != 'some_name')

        :returns: Lazy query result object.

        .. seealso:: :class:`infinisdk.core.object_query.ObjectQuery`
        """
        return self.object_type.find(self.system, *predicates, **kw)

    def get_all(self):
        return self.find()

    def get_by_id(self, id):
        """
        Obtains an object with a specific id
        """
        return self.get(id=id)

    def safe_get_by_id(self, id):
        """
        Like get_by_id, only returning None if the object could not be found
        """
        return self.safe_get(id=id)

    def get_by_id_lazy(self, id):
        """
        Obtains an object with a specified id *without* checking if it exists or querying it on the way.

        This is useful assuming the next operation is a further query/update on this object.
        """
        # TODO: test this on components
        return self.object_type.construct(self.system, {self.fields.id.api_name:id})

    def get(self, *predicates, **kw):
        """
        Finds exactly one object matching criteria. Raises :class:`.ObjectNotFound` if not found, :class:`.TooManyObjectsFound` if more than one is found
        """
        returned = self.find(*predicates, **kw)
        if not returned:
            raise ObjectNotFound()
        if len(returned) > 1:
            raise TooManyObjectsFound()
        [obj] = returned
        return obj

    def safe_get(self, *predicates, **kw):
        """
        Like :meth:`.TypeBinder.get`, only returns ``None`` if no objects were found
        """
        try:
            return self.get(*predicates, **kw)
        except ObjectNotFound:
            return None

    def choose(self, *predicates, **kw):
        """
        Chooses a random element out of those returned. Raises ObjectNotFound if none were returned
        """
        returned = self.find(*predicates, **kw)
        if not returned:
            raise ObjectNotFound()

        return returned[random.randrange(len(returned))]

    def safe_choose(self, *predicates, **kw):
        """
        Like choose, but returns None when not found
        """
        try:
            return self.choose(*predicates, **kw)
        except ObjectNotFound:
            return None

    def count(self, *predicates, **kw):
        return len(self.find(*predicates, **kw).page_size(1))

    def __repr__(self):
        return "<{0}.{1}>".format(self.system, self.object_type.get_plural_name())

    def __iter__(self):
        return iter(self.find())

    @deprecated(message="Use to_list/count instead")
    def __len__(self):
        return len(self.find())

    def to_list(self):
        """Returns the entire set of objects as a Python list

        .. caution:: Queries are lazy by default to avoid heavy API calls and repetitive page
          requests. Using ``to_list`` will forcibly iterate and fetch all objects, which might
          be a very big collection. This can cause issues like slowness and memory exhaustion
        """
        return self.get_all().to_list()

