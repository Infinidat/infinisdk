import abc
from munch import Munch
from .api import API
from ..type_binder_container import TypeBinderContainer


class APITarget(metaclass=abc.ABCMeta):
    """
    Abstract base class for anything that would like to become an API target
    """
    OBJECT_TYPES = []
    SYSTEM_EVENTS_TYPE = None
    SYSTEM_COMPONENTS_TYPE = None

    def __init__(self, address, auth=None, use_ssl=False, ssl_cert=None):
        """
        :param address: Either a tuple of (host, port), or a list of such tuples for multiple addresses
        """
        if self._is_simulator(address):
            address = self._get_simulator_address(address, use_ssl=use_ssl)
        self._addresses = self._normalize_addresses(address, use_ssl)

        self.objects = TypeBinderContainer(self)

        if auth is None:
            auth = self._get_api_auth()  # pylint: disable=assignment-from-none

        self.api = API(self, auth, use_ssl=use_ssl, ssl_cert=ssl_cert)
        self.api.set_request_default_timeout(self._get_api_timeout())

        self.types = Munch()

        self._initialize()
        self._caching_enabled = True

    def _initialize(self):
        for object_type in self.OBJECT_TYPES:
            self.objects.install(object_type)
            self.types[object_type.get_type_name()] = self.types[object_type.__name__] = object_type

        self.components = self.SYSTEM_COMPONENTS_TYPE(self)  # pylint: disable=not-callable
        self.events = self.SYSTEM_EVENTS_TYPE(self)  # pylint: disable=not-callable

    def _get_api_auth(self):
        return None

    def is_field_supported(self, field):  # pylint: disable=unused-argument
        return True

    def disable_caching(self):
        """Disables field caching, and causes each field fetching to fetch the actual up-to-date value from the system
        """
        self._caching_enabled = False

    def enable_caching(self):
        """Enables field caching, and causes each field fetching to use the cache by default
        """
        self._caching_enabled = True

    def is_caching_enabled(self):
        """Returns whether caching is currently enabled
        """
        return self._caching_enabled

    def check_version(self):
        """Called automatically by the API on the first request made to the system. Should fetch and verify the
        system version to make sure it can be operated against.
        """
        raise NotImplementedError() # pragma: no cover

    def get_collections_names(self):
        return [obj_type.get_plural_name() for obj_type in self.OBJECT_TYPES]

    def get_collections(self):
        return [obj_type for obj_type in self.objects]

    def _normalize_addresses(self, addresses, use_ssl):
        if not isinstance(addresses[0], (list, tuple)):
            addresses = [addresses]

        default_port = 443 if use_ssl else 80
        returned = []
        for address in addresses:
            if not isinstance(address, tuple):
                address = (address, default_port)
            if len(address) != 2:
                raise ValueError("Invalid address specified: {!r}".format(address))
            returned.append(address)
        return returned

    def get_approval_failure_codes(self):
        return tuple()

    def get_api_addresses(self):
        return self._addresses

    def get_api_timeout(self):
        return self.api.get_request_default_timeout()

    def get_api_auth(self):
        return self.api.get_auth()

    def _get_received_name_or_ip(self):
        return self._addresses[0][0]

    def __repr__(self):
        return self._get_received_name_or_ip()

    def _is_simulator(self, address):
        raise NotImplementedError() # pragma: no cover

    def _get_simulator_address(self, address, use_ssl):
        raise NotImplementedError() # pragma: no cover

    def _get_api_timeout(self):
        """
        :returns: number of seconds to wait for a command to return before raising a timeout
        """
        raise NotImplementedError() # pragma: no cover

    @classmethod
    def get_type_name(cls):
        return cls.__name__
