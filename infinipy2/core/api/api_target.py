import abc
from ..._compat import with_metaclass

class APITarget(with_metaclass(abc.ABCMeta)):
    """
    Abstract base class for anything that would like to become an API target
    """

    def get_api_addresses(self):
        """
        :rtype: list of tuples of (ip address, port) for api interaction
        """
        raise NotImplementedError() # pragma: no cover

    def get_api_timeout(self):
        """
        :rtype: number of seconds to wait for a command to return before raising a timeout
        """
        raise NotImplementedError() # pragma: no cover

    def get_api_auth(self):
        """
        :rtype: tuple of (username, password) to be used by default
        """
        raise NotImplementedError() # pragma: no cover
