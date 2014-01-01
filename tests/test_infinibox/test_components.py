import random
from infinipy2._compat import string_types
from ..utils import InfiniBoxTestCase
from infinipy2.infinibox.components import (System, Rack, Enclosure,
                                            Drive, FcPort, Node, Service)
from infinipy2.core.config import config

NO_OF_ENCLOSURES_DRIVES = config.get_path('infinibox.defaults.enlosure_drives.total_count.mock')

def choose_from_list(a_list):
    return a_list[random.randrange(len(a_list))]

class ComponentsTest(InfiniBoxTestCase):
    def _basic_check_for_component(self, component_type, parent_type, check_sub_components):
        sys_components = self.system.components
        from_types_list = getattr(sys_components.types, component_type.__name__)
        self.assertIs(from_types_list, component_type)

        collection = sys_components[component_type.get_plural_name()]
        component_instances = collection.get_all()

        is_component_instance = lambda obj: isinstance(obj, component_type)
        self.assertTrue(all(map(is_component_instance, component_instances)))

        # FIXME: HACK until there will be a simulator... (Reason: Mock doesn't have drives & fc_ports)
        if component_type in [Drive, FcPort]:
            return

        component_instance = collection.choose()

        if parent_type:
            parent_obj = component_instance.get_parent()
            self.assertTrue(isinstance(parent_obj, parent_type))

        if check_sub_components:
            sub_components = component_instance.get_sub_components()
            is_sub_component = lambda obj: is_component_instance(obj.get_parent())
            self.assertTrue(all(map(is_sub_component, sub_components)))

    def test_system_component_does_not_perform_api_get(self):
        self.system.api = None
        system_component = self.system.components.system_component
        self.assertEquals(system_component.get_index(), 0)

    def test_get_component_by_id_lazily(self):
        rack_1_id = ('system', 0, 'rack', 1)
        with self.assertRaises(NotImplementedError):
            self.system.components.get_by_id_lazy(rack_1_id)
        self.system.components.enclosures.choose()  # Initializing components...

        component = self.system.components.get_by_id_lazy(rack_1_id)
        self.assertEqual(component.get_index(), 1)
        self.assertEqual(component.get_type_name(), 'rack')

    def test_system_component(self):
        self._basic_check_for_component(System, None, False)
        system_component = self.system.components.system_component
        self.assertIs(system_component, self.system.components.systems.get())
        self.assertTrue(isinstance(system_component.get_state(), string_types))

    def test_rack_component(self):
        self._basic_check_for_component(Rack, None, True)

    def test_enclosure_component(self):
        self._basic_check_for_component(Enclosure, Rack, True)
        enc = self.system.components.enclosures.choose()
        self.assertTrue(isinstance(enc.get_state(), string_types))

    def test_drive_component(self):
        self._basic_check_for_component(Drive, Enclosure, False)
        all_drives = self.system.components.drives.find()
        self.assertEquals(len(all_drives), NO_OF_ENCLOSURES_DRIVES)

    def test_fc_port_component(self):
        self._basic_check_for_component(FcPort, Node, False)

    def test_node_component(self):
        self._basic_check_for_component(Node, Rack, True)
        node = self.system.components.nodes.choose()
        self.assertTrue(isinstance(node.get_state(), string_types))

    def test_service_component(self):
        self._basic_check_for_component(Service, Node, False)
