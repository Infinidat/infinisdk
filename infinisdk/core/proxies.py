class ValueProxy:
    """
    Represents a value that is fetched at a later stage from various sources
    """

    def resolve(self):
        raise NotImplementedError() # pragma: no cover

class FROM_CONFIG:
    """
    Values fetched from configuration
    """

    def __init__(self, path):
        super(FROM_CONFIG, self).__init__()
        self._path = path

    def resolve(self):
        raise NotImplementedError() # pragma: no cover
