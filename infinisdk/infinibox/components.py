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
from .._compat import string_types
from ..core.field import Field
from ..core.system_component import SystemComponentsBinder
from ..core.system_object import SystemObject
from infi.pyutils.lazy import cached_method
from .component_query import InfiniBoxComponentQuery

from urlobject import URLObject as URL

class InfiniBoxSystemComponents(SystemComponentsBinder):

    def __init__(self, system):
        super(InfiniBoxSystemComponents, self).__init__(InfiniBoxSystemComponent, system)
        self.system_component = System(self.system, {'parent_id': "", 'index': 0})
        self.cache_component(self.system_component)
        Rack = self.racks.object_type
        self._rack_1 = Rack(self.system, {'parent_id': self.system_component.id, 'rack': 1})
        self.cache_component(self._rack_1)
        self._fetched_nodes = False
        self._fetched_others = False

    def should_fetch_nodes(self):
        return not self._fetched_nodes

    def should_fetch_all(self):
        return not self._fetched_others

    def mark_fetched_nodes(self):
        self._fetched_nodes = True

    def mark_fetched_all(self):
        self._fetched_others = True
        self._fetched_nodes = True

    def get_rack_1(self):
        return self._rack_1


class ComputedIDField(Field):
    def compute_obj_id(self, obj_index, parent_id, obj_class):
        index_str = obj_index if isinstance(obj_index, string_types) else "{0:02}".format(obj_index)
        return "{0}{1}{2}:{3}".format(parent_id,
                                      "_" if parent_id else "",
                                      obj_class.get_type_name(),
                                      index_str)

    def extract_from_json(self, obj_class, json):
        curr_index = obj_class.fields.index.extract_from_json(obj_class, json)
        parent_id = json[obj_class.fields.parent_id.api_name]
        return self.compute_obj_id(curr_index, parent_id, obj_class)


class InfiniBoxSystemComponent(SystemObject):
    BINDER_CLASS = SystemComponentsBinder
    BASE_URL = URL("components")
    FIELDS = [
        ComputedIDField("id", is_identity=True, cached=True),
        Field("parent_id", cached=True, add_updater=False, is_identity=True),
    ]

    def get_parent(self):
        return self.system.components.try_get_component_by_id(self.get_parent_id())

    @cached_method
    def get_this_url_path(self):
        parent_url = self.get_parent().get_this_url_path()
        this_url = parent_url.add_path(self.get_plural_name()).add_path(str(self.get_index()))
        return this_url

    @classmethod
    def get_url_path(cls, system):
        # Currently there is no url, in infinibox, to get all instances of specific component
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    def get_type_name(cls):
        return cls.__name__.lower()

    @classmethod
    def get_plural_name(cls):
        return "{0}s".format(cls.get_type_name())

    @classmethod
    def find(cls, system, *predicates, **kw):
        return InfiniBoxComponentQuery(system, cls, *predicates, **kw)

    @classmethod
    def _get_sub_components_classes(cls):
        return []

    def get_sub_components(self):
        return self.system.components.find(parent_id=self.id)

    def refresh(self):
        data = self.system.api.get(self.get_this_url_path()).get_json()['result']
        self.construct(self.system, data, self.get_parent_id())

    @classmethod
    def construct(cls, system, data, parent_id):
        data['parent_id'] = parent_id
        component_id = cls.fields.id.extract_from_json(cls, data)
        returned = system.components.try_get_component_by_id(component_id)
        if returned is None:
            component_type = cls.get_type_name()
            object_type = system.components._COMPONENTS_BY_TYPE_NAME.get(component_type, InfiniBoxSystemComponent)
            returned = object_type(system, data)
            system.components.cache_component(returned)
        else:
            returned.update_field_cache(data)
        for sub_class in returned._get_sub_components_classes():
            for sub_class_data in data[sub_class.get_plural_name()]:
                sub_class.construct(system, sub_class_data, component_id)
        return returned


@InfiniBoxSystemComponents.install_component_type
class Rack(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="rack", type=int, is_identity=True, cached=True),
    ]

    @classmethod
    def get_specific_rack_url(cls, rack_id):
        racks_url = cls.BASE_URL.add_path(cls.get_plural_name())
        return racks_url.add_path(str(rack_id))

    @cached_method
    def get_this_url_path(self):
        return self.get_specific_rack_url(self.get_index())

    @classmethod
    def _get_sub_components_classes(cls):
        return [Enclosure, Node]

@InfiniBoxSystemComponents.install_component_type
class Enclosure(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, is_identity=True, cached=True),
        Field("drives", type=list),
        Field("state"),
    ]

    @classmethod
    def _get_sub_components_classes(cls):
        return [Drive]

@InfiniBoxSystemComponents.install_component_type
class Node(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="id", type=int, is_identity=True, cached=True),
        Field("name"),
        Field("fc_ports", type=list),
        Field("drives", type=list),
        Field("state"),
    ]

    @classmethod
    def get_url_path(cls, system):
        return cls.BASE_URL.add_path(cls.get_plural_name())

    @classmethod
    def _get_sub_components_classes(cls):
        return [FcPort, Service]

@InfiniBoxSystemComponents.install_component_type
class FcPort(InfiniBoxSystemComponent):
    FIELDS = [
        Field("wwpn", is_identity=True),
        Field("index", api_name="id", type=int, cached=True),
        Field("node", cached=True),
        Field("state"),
    ]

    @classmethod
    def get_type_name(self):
        return "fc_port"

@InfiniBoxSystemComponents.install_component_type
class Drive(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="drive_index", type=int, is_identity=True, cached=True),
        Field("enclosure_index", type=int, cached=True),
        Field("serial_number"),
        Field("state"),
    ]

@InfiniBoxSystemComponents.install_component_type
class Service(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", api_name="name", is_identity=True, cached=True),
        Field("state"),
    ]

@InfiniBoxSystemComponents.install_component_type
class System(InfiniBoxSystemComponent):
    FIELDS = [
        Field("index", cached=True),
        Field("state", add_getter=False),
    ]

    @cached_method
    def get_this_url_path(self):
        return URL('system')

    def get_state(self):
        return self.get_field('operational_state')['state']
