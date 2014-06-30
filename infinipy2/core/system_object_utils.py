def make_getter(attribute_name):
    def getter(self, **kwargs):
        return self.get_field(attribute_name, **kwargs)

    getter.__name__ = "get_{0}".format(attribute_name)
    getter.__doc__ = "obtains the value of {0!r}".format(attribute_name)
    return getter

def make_updater(attribute_name):
    def updater(self, value, **kwargs):
        return self.update_field(attribute_name, value, **kwargs)

    updater.__name__ = "update_{0}".format(attribute_name)
    updater.__doc__ = "updates the value of {0!r}".format(attribute_name)
    return updater

def make_getter_updater(attribute_name):
    return make_getter(attribute_name), make_updater(attribute_name)
