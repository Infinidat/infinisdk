class TypeInfo(object):

    def __init__(self, type, min_length=None, max_length=None, charset=None, max=None, min=None):
        super(TypeInfo, self).__init__()
        self.type = type

        #: minimum length for parameter
        self.min_length = min_length
        #: maximum length for parameter
        self.max_length = max_length
        if charset is not None:
            charset = set(charset)
        #: sequence of characters the parameter must use
        self.charset = charset
        #: minimum value
        self.min = min
        #: maximum value
        self.max = max

    def is_valid_value(self, value):
        """
        Checks if a given value is valid given the type constraints
        """
        result, reason = self.is_valid_value_explain(value)
        return result

    def is_valid_value_explain(self, value):
        """
        :rtype: A tuple of (is_valid, reason)
        """
        if type(value) is not self.type:
            return (False, "Invalid type")

        if self.charset and not set(value).issubset(self.charset):
            return (False, "Invalid characters")

        if self.min is not None and value < self.min:
            return (False, "Under minimum value")

        if self.max is not None and value > self.max:
            return (False, "Exceeds maximum value")

        if self.min_length is not None and len(value) < self.min_length:
            return (False, "Too short")

        if self.max_length is not None and len(value) > self.max_length:
            return (False, "Too long")

        return (True, None)
