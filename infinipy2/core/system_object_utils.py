def make_getter(attribute_name):
    def getter(self, *args, **kwargs):
        return self.get_field(attribute_name, *args, **kwargs)

    getter.__name__ = "get_{}".format(attribute_name)
    getter.__doc__ = "obtains the value of {!r}".format(attribute_name)
    return getter
