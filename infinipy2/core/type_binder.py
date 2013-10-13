import random
from .exceptions import ObjectNotFound, TooManyObjectsFound

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

    def find(self, *predicates, **kw):
        """
        Returns all objects with desired predicates.

        Proxy for :func:`.SystemObject.find`.
        """
        return self.object_type.find(self.system, *predicates, **kw)

    def get_by_id_lazy(self, id):
        """
        Obtains an object with a specified id *without* checking if it exists or querying it on the way.

        This is useful assuming the next operation is a further query/update on this object.
        """
        # TODO: test this on components
        return self.object_type(self.system, {"id":id})

    def get(self, *predicates, **kw):
        """
        Finds exactly one object matching criteria. Raises :class:`ObjectNotFound` if not found, :class:`TooManyObjectsFound` if more than one is found
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
        Like :func:`.get`, only returns ``None`` if no objects were found
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

    def count(self, *predicates, **kw):
        return len(self.find(*predicates, **kw))

    def __repr__(self):
        return "<{0}.{1}>".format(self.system, self.object_type.get_plural_name())

    def __iter__(self):
        return iter(self.find())

    def __len__(self):
        return len(self.find())
