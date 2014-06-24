###!
### Infinidat Ltd.  -  Proprietary and Confidential Material
### 
### Copyright (C) 2014, Infinidat Ltd. - All Rights Reserved
### 
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
### 
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
###!
def make_getter(attribute_name):
    def getter(self, *args, **kwargs):
        return self.fields.get(attribute_name).binding.get_api_value_from_object(self, *args, **kwargs)

    getter.__name__ = "get_{0}".format(attribute_name)
    getter.__doc__ = "obtains the value of {0!r}".format(attribute_name)
    return getter

def make_updater(attribute_name):
    def updater(self, *args, **kwargs):
        return self.fields.get(attribute_name).binding.set_object_value_from_api(self, *args, **kwargs)

    updater.__name__ = "update_{0}".format(attribute_name)
    updater.__doc__ = "updates the value of {0!r}".format(attribute_name)
    return updater

def make_getter_updater(attribute_name):
    return make_getter(attribute_name), make_updater(attribute_name)
