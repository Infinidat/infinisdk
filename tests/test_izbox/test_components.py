from ..utils import TestCase
from infinipy2._compat import string_types

class ComponentsTest(TestCase):


    def test_components_find(self):
        self.assertEquals(len(self.system.components.enclosures.find()), 8)

        self.assertEquals(0, len(self.system.components.enclosures.find(self.system.components.enclosures.fields.status != "OK")))

    def test_component_is_always_same_object(self):
        enclosures = self.system.components.enclosures
        candidates = [
            enclosures.get_by_id_lazy(102000),
            enclosures.get_by_id_lazy(102000),
            enclosures.get(id=102000),
            enclosures.get(id=102000),
            enclosures.safe_get(id=102000),
            ]
        self.assertEquals(
            len(set(id(x) for x in candidates)), 1,
            "Objects are unexpectedly recreated for each fetch"
        )

    def test_component_types(self):
        from infinipy2.izbox.components import System, Enclosure, EnclosureDrive
        self.assertIs(self.system.components.types.System, System)
        self.assertIs(self.system.components.types.Enclosure, Enclosure)
        self.assertIs(self.system.components.types.EnclosureDrive, EnclosureDrive)

    def test_components_getitem(self):
        self.assertIs(self.system.components["nodes"], self.system.components.nodes)
        self.assertIs(self.system.components[self.system.components.types.Node], self.system.components["nodes"])

    def test_components_choose(self):
        enc = self.system.components.enclosures.choose()
        node = self.system.components.nodes.choose()
        self.assertTrue(enc.is_ok())
        self.assertTrue(node.is_ok())

    def test_enclosure_drives(self):
        self.assertEquals(len(self.system.components.enclosure_drives.find()), 480) #capped for scenario maintainability

    def test_find_all_components(self):
        self.assertGreater(len(self.system.components.find()), 480)

    def test_system_component(self):
        system_component = self.system.components.systems.get()
        self.assertIs(system_component, self.system.components.system_component)
        self.assertIn('system_serial', system_component.get_additional_data())

    def test_system_component_does_not_perform_api_get(self):
        self.system.api = None
        system_component = self.system.components.system_component
        self.assertEquals(system_component.id, 0)

    def test_system_get_primary_secondary_nodes(self):
        self.assertIs(self.system.components.system_component.get_primary_node(), self.system.components.nodes.get(index=1))
        self.assertIs(self.system.components.system_component.get_secondary_node(), self.system.components.nodes.get(index=2))

        for is_primary, node in [
                (True, self.system.components.system_component.get_primary_node()),
                (False, self.system.components.system_component.get_secondary_node())
        ]:
            self.assertEquals(is_primary, node.is_primary())
            self.assertEquals(not is_primary, node.is_secondary())

    def test_cannot_get_system_component_by_id_lazily(self):
        with self.assertRaises(NotImplementedError):
            self.system.components.get_by_id_lazy(1)

    def test_get_alert_types(self):
        alert_types = self.system.components.get_alert_types()
        self.assertTrue(isinstance(alert_types, list))
        self.assertIsNot(alert_types[0].get('code'), None)

    def test_get_type_info_from_system(self):
        type_info = self.system.components.get_type_infos_from_system()
        self.assertIn('node', type_info)

    def test_get_parent_and_sub_components(self):
        enc = self.system.components.enclosures.choose()
        with self.assertRaises(NotImplementedError):
            enc.get_parent()

        rack_1 = self.system.components.racks.choose()
        enc_parent = enc.get_parent()
        self.assertEqual(rack_1, enc_parent)
        self.assertIn(enc, rack_1.get_sub_components())

    def test_get_node_address(self):
        node = self.system.components.nodes.choose()
        node_address = node.get_address()
        self.assertTrue(isinstance(node_address, string_types))

    def test_service(self):
        service = self.system.components.services.choose()
        self.assertTrue(isinstance(service.get_name(), string_types))
