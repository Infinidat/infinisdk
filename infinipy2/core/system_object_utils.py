def make_getter(attribute_name):
    def getter(self, *args, **kwargs):
        return self.get_field(attribute_name, *args, **kwargs)

    getter.__name__ = "get_{}".format(attribute_name)
    getter.__doc__ = "obtains the value of {!r}".format(attribute_name)
    return getter

def make_updater(attribute_name):
    def updater(self, *args, **kwargs):
        return self.update_field(attribute_name, *args, **kwargs)

    updater.__name__ = "update_{}".format(attribute_name)
    updater.__doc__ = "updates the value of {!r}".format(attribute_name)
    return updater
