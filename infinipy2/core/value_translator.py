class ValueTranslator(object):
    """
    This is an abstract base for translator objects.

    Translator objects are used to convert values to and from the system's API layer
    """

    def to_api(self, value):
        """
        Translates a value from Python to its API/json representation

        :rtype: must be JSON encodable
        """
        return self._to_api(value)

    def from_api(self, value):
        """
        Translates a value from the system API to its Pythonic counterpart
        """
        return self._from_api(value)

    def _to_api(self, value):
        raise NotImplementedError() # pragma: no cover

    def _from_api(self, value):
        raise NotImplementedError() # pragma: no cover

class FunctionTranslator(ValueTranslator):
    """
    Implements value translation with the use of functions
    """

    def __init__(self, to_api, from_api):
        super(FunctionTranslator, self).__init__()
        self._to_api = to_api
        self._from_api = from_api

class IdentityTranslator(ValueTranslator):
    def identity(self, value):
        return value

    to_api = from_api = identity
