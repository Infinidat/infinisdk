from ..core.field import Field
from ..core.system_component import SystemComponentsBinder
from ..core.system_object import SystemObject
from infi.pyutils.lazy import cached_method

from urlobject import URLObject as URL


class InfiniBoxSystemComponents(SystemComponentsBinder):

    def __init__(self, system):
        super(InfiniBoxSystemComponents, self).__init__(InfiniBoxSystemComponents, system)
        self.system_component = System(self.system, {"type": "system", "id": 0})
        self.cache_component(self.system_component)

    @classmethod
    def get_type_name(cls):
        return "component"

    @classmethod
    def get_plural_name(cls):
        return "{}s".format(cls.get_type_name())


class InfiniBoxSystemComponent(SystemObject):
    BINDER_CLASS = SystemComponentsBinder

    FIELDS = [
        Field("id", type=int, is_identity=True),
        Field("state"),
    ]

    def is_active(self):
        return self.get_state().lower() == "ACTIVE"

    def get_additional_data(self):
        return self.get_field("data", from_cache=True)

    def get_parent(self):
        raise NotImplementedError()  # pragma: no cover

    def get_sub_components(self):
        raise NotImplementedError()  # pragma: no cover

    @cached_method
    def get_this_url_path(self):
        parent_url = self.get_parent().get_this_url_path()
        this_url = parent_url.add_path(self._get_plural_name()).add_path(str(self.id))
        return this_url

    @classmethod
    def get_url_path(cls, system):
        returned = URL("/api/rest/components")
        if cls is not system.components.object_type:
            returned = returned.add_query_param("type", "eq:{}".format(cls.get_type_name()))
        return returned

    @classmethod
    def get_type_name(cls):
        return cls.__name__.lower()

    @classmethod
    def get_plural_name(cls):
        return "{}s".format(cls.get_type_name())

    @classmethod
    def construct(cls, system, data):
        component_id = data["id"]
        returned = system.components.try_get_component_by_id(component_id)
        if returned is None:
            component_type = data["type"]
            object_type = system.components._COMPONENTS_BY_TYPE_NAME.get(component_type, InfiniBoxSystemComponent)
            returned = object_type(system, data)
            system.components.cache_component(returned)
        else:
            returned.update_field_cache(data)
        return returned


@InfiniBoxSystemComponents.install_component_type
class System(InfiniBoxSystemComponent):
    pass
