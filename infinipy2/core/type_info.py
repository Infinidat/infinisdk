class TypeInfo(object):

    def __init__(self, type, min_length=None, max_length=None, charset=None, max=None, min=None):
        """
        :param min_length: minimum length for parameter
        :param max_length: maximum length for parameter
        :param charset: sequence of characters the parameter must use
        :param min: minimum value
        :param max: maximum value
        """
        super(TypeInfo, self).__init__()
        self.type = type
        self.min_length = min_length
        self.max_length = max_length
        if charset is not None:
            charset = set(charset)
        self.charset = charset
        self.min = min
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
